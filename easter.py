from datetime import datetime, timezone, timedelta
from math import ceil, floor
from skyfield import almanac, timelib, api
import pprint


# ts = None
# e = None
sky_load = api.Loader('./sky_data')
ts = sky_load.timescale()  # timescale
e = sky_load('de438.bsp')

# write code to automatically propagate these dates
init_year = None
last_year = None
start_second = None
end_second = None

equinox_day = 21
equinox_month = 3

# full_moon = datetime(2019,5,18,21,11,tzinfo=timezone.utc)
# test_date = datetime(2019,3,20,tzinfo=timezone.utc)
# print(test_date.date())


def march_equinox(year):
    # must be 15 day range minimum, apparently?
    t0 = ts.utc(year, 3, 13)
    t1 = ts.utc(year, 3, 28)
    tstamp, phase = almanac.find_discrete(t0, t1, almanac.seasons(e))
    for phi, ti in zip(phase, tstamp):
        if phi == 0:
            return ti.utc_datetime()
    else:
        raise ExceptionalError("Is this Earth?")


# next full moon from given data
def next_full_moon(given_date):
    start = ts.utc(given_date)
    finish = ts.utc(given_date + timedelta(30))
    times, phases = almanac.find_discrete(start, finish, almanac.moon_phases(e))
    for t, p in zip(times, phases):
        if p == 2:
            return t.utc_datetime()
    else:
        raise ExceptionalError("That's no moon.")  # there should always be a full moon over the span of 30 days


# holistic approach, functions from 1550 up to 2650 - JD 2287184.5 through 2688976.5
def astronomical_easter(year):
    full_moon = next_full_moon(march_equinox(year)+timedelta(1))  # next full moon following equinox
    for i in range(7):  # find next sunday
        day = (full_moon + timedelta(i))
        if day.weekday() == 6:  # 6 == sunday
            return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)


# https://en.wikipedia.org/wiki/Computus#Software
# Ian Taylor
def gauss_easter(year):
    """
    Gauss algorithm to calculate the date of easter in a given year
    returns a date object
    """
    a = year % 19
    b = year >> 2
    c = b // 25 + 1
    d = (c * 3) >> 2
    e = ((a * 19) - ((c * 8 + 5) // 25) + d + 15) % 30
    e += (29578 - a - e * 32) >> 10
    e -= ((year % 7) + b - d + e + 2) % 7
    d = e >> 5
    day = e - d * 31
    month = d + 3
    return datetime(year, month, day, tzinfo=timezone.utc)


# later = 1, earlier = -1, during = 0
# Check data range, see if it falls outside
def outside_data_range(year):
    if year > last_year:
        return 1
    elif year < init_year:
        return -1
    else:
        return 0


# returns True if data is inside, else raises (not super helpful) exception
def in_data_range(year):  # I don't know what I'm doing
    odr = outside_data_range(year)
    if not odr:  # if it is outside the data range
        raise ValueError(f"The year {year} falls outside of data range.")
    return True


# compare all years from a point
def compare_easters(first_year=init_year, final_year=last_year, print_results=False):
    easter_dates = {}
    if print_results:
        print("Years which differ:")
        print("YYYY - Astronomy vs. The Church (DD/MM)")
    
    # cur_year = datetime.now().year

    for i in range(first_year, final_year+1):
        astronomy, the_church, diff_days = compare_easter(i)
        easter_dates[i] = {'Church': the_church, 'Astronomy': astronomy}
        if diff_days != 0:
            # if you want to print a fun little comparison to console
            if print_results:
                ast_date = astronomy.strftime('%d/%m')
                ch_date = the_church.strftime('%d/%m')
                diff_abs = abs(diff_days)
                diff_extra = "a week" if (diff_abs == 7) else f"{diff_abs} days"
                diff_tense = 'late.' if diff_days < 0 else 'early.'
                date_stuff = f"{i} - {ast_date} vs. {ch_date}"
                comp_stuff = f"Easter is {diff_extra} {diff_tense}"
                print(f"{date_stuff} - {comp_stuff}")
    return easter_dates


# compare a specific year
def compare_easter(year, print_results=False):
    astronomy = astronomical_easter(year)
    the_church = gauss_easter(year)
    diff = astronomy - the_church
    if print_results:
        ast_date = astronomy.strftime('%d/%m/%y')
        ch_date = the_church.strftime('%d/%m/%y')
        print(f"Science vs Church : {ast_date} | {ch_date}")
    else:
        return astronomy, the_church, diff.days

# helper functions


# returns data range as two datetime objects (start and end), utc timezone
# also returns exact j2000 seconds
def get_data_range(dataset):
    first_second = dataset.spk.segments[0].start_second
    last_second = dataset.spk.segments[0].end_second
    start = ts.tt(jd=dataset.spk.segments[0].start_jd).utc_datetime()
    end = ts.tt(jd=dataset.spk.segments[0].end_jd).utc_datetime()
    return start, end, first_second, last_second


# check if data range is set: if not, sets it
def dr_check(dataset):
    if not (init_year or last_year):
        set_data_range(dataset)
        return False
    return True


def jd_convert(seconds):
    T0 = 2451545.0
    S_PER_DAY = 86400.0
    """Convert a number of seconds since J2000 to a Julian Date."""
    return T0 + seconds / S_PER_DAY

        
class ExceptionalError(Exception):
    """Raised when there should be no way to reach this point."""
    pass


# pulled from spk, start and end dates of data date range
def set_data_range(dataset):
    global init_year, last_year, start_second, end_second
    init_year, last_year, start_second, end_second = get_data_range(dataset)


def main():
    print("We're live.")
    set_data_range(e)
    print(f"Start Year: {init_year}, End Year: {last_year}")
    pprint.pprint(compare_easters(2000, 2025, print_results=False))


if __name__ == '__main__':
    main()
