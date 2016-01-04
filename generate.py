#!/usr/bin/env python3
"""
Generate a Dutch week calendar for an entire year.

The generated calendar is in odt format.

This script accepts a YAML data file which must contain the fields
``special dates``, ``birthdays`` and ``weddings``.

Example data file

.. code-block:: yaml

    year: 2016

    special dates:
      03-04: May the Fourth be with you
      03-05: Revenge of the Fifth

    birthdays:
      1991-01-11:
        - Remco
      1991-08-25:
        - Linux

    weddings:
      2006-06-06
         - - Husband
           - Wife

"""
import argparse
import contextlib
import datetime
import locale
import os
import warnings

import yaml
from dateutil import easter
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from relatorio.templates.opendocument import Template


class BadConfigError(Exception):
    """
    Raised when an invalid configuration is found.

    """


def start_date(year):
    """
    Find the first day of the first week of the given year.

    Args:
        year (int): The for which to find the first day of its first week.

    Returns:
        datetime.date: The first day of the first week of the given year.

    """
    jan_01 = datetime.date(year, 1, 1)
    return jan_01 - datetime.timedelta(days=jan_01.weekday())


def holiday(date):
    """
    Return if the given date is a holiday.

    Args:
        date (datetime.date): The date for which to check if it's a holiday.

    Returns:
        str: The Dutch name of the holiday on that date or an empty string.

    """
    # Simple hardcoded dates
    if date.month == 1:
        if date.day == 1:
            return 'Nieuwjaar'
        if date.day == 6:
            return 'Drie Koningen'
    if date.month == 2:
        if date.day == 14:
            return 'Valentijn'
    if date.month == 4:
        if date.day == 27:
            return 'Koningsdag'
    if date.month == 5:
        if date.day == 4:
            return 'Dodenherdenking'
        if date.day == 5:
            return 'Bevrijdingsdag'
    if date.month == 7:
        if date.day == 29:
            return 'Frikandellendag'
    if date.month == 10:
        if date.day == 4:
            return 'Dierendag'
    if date.month == 12:
        if date.day == 5:
            return 'Sinterklaas'
        if date.day == 25:
            return 'Eerste Kerstdag'
        if date.day == 26:
            return 'Tweede Kerstdag'
        if date.day == 31:
            return 'Oudjaar'

    # Nth sunday of month
    if date.month == 3 and date.weekday() == 6 and date.day > 24:
        return ('Zomertijd\n'
                'Vergeet niet je klok niet een uur vooruit te zetten!')
    if date.month == 5 and date.weekday() == 6 and 7 < date.day < 15:
        return 'Moederdag'
    if date.month == 6 and date.weekday() == 6 and 14 < date.day < 22:
        return 'Vaderdag'
    if date.month == 9 and date.weekday() == 1 and 15 < date.day < 23:
        return 'Prinsjesdag'
    if date.month == 10 and date.weekday() == 6 and date.day > 24:
        return 'Wintertijd\nVergeet niet je klok een uur terug te zetten!'

    # Easte related
    easter_date = easter.easter(date.year)
    if date == easter_date:
        return 'Eerste Paasdag'
    if date == easter_date + datetime.timedelta(days=-2):
        return 'Goede Vrijdag'
    if date == easter_date + datetime.timedelta(days=1):
        return 'Tweede Paasdag'
    if date == easter_date + datetime.timedelta(days=39):
        return 'Hemelvaart'
    if date == easter_date + datetime.timedelta(days=49):
        return 'Eerste Pinksterdag'
    if date == easter_date + datetime.timedelta(days=50):
        return 'Tweede Pinksterdag'

    carnaval_date = easter_date
    i = 40  # Carnaval is 40 days before easter
    while i:
        # Sundays don't count towards these 40 days
        if carnaval_date.weekday() != 6:
            i -= 1
        carnaval_date -= datetime.timedelta(days=1)
    for i in range(3):
        if date == carnaval_date - datetime.timedelta(days=i):
            return 'Carnaval'
    return ''


def process_birthdays(date, birthdays):
    """
    Find and parse birthdays for the given date.

    Args:
        date (datetime.date): The date to process.
        birthdays (dict): A mapping of birthdays to an iterable of names
            whose birthday it is.

    Yields:
        dict: A dict containing a persons name and age.

    """
    for birthdate, names in birthdays.items():
        if birthdate.month == date.month and birthdate.day == date.day:
            for name in names:
                yield dict(
                    name=name,
                    age=date.year - birthdate.year
                )


def process_weddings(date, weddings):
    """
    Find and parse weddings for the given date.

    Args:
        date (datetime.date): The date to process.
        weddings (dict): A mapping of wedding dates to an iterable of
            iterables of names in that marriage.

    Yields:
        dict: A dict containing the age of the marriage and the names
            joined to one string.

    """
    for wedding_date, couples in weddings.items():
        if wedding_date.month == date.month and wedding_date.day == date.day:
            for couple in couples:
                yield dict(
                    names=' & '.join(couple),
                    age=date.year - wedding_date.year
                )


def day_to_dict(date, birthdays, weddings, special_dates):
    """
    Convert a date to a dict of usable fields.

    Args:
        date (datetime.date): The date to process.
        birthdays (dict): A dict of dates mapped to birthdays.
        weddings (dict): A dict of dates mapped to wedding dates.
        special_dates (dict): A dict mapping a date in the form '%m-%d'
            to a special string to render.

    Returns:
        dict: A dict containing:

        :day: The day of the month.
        :month: The month of the date as a long string.
        :short_month: The month of the date as a short lower case string.
        :week_day: The day of the week as a long capitalized string.
        :events: A list of strings representing the events on that day.

    """
    events = []
    hol = holiday(date)
    if hol:
        events.append(hol)
    with contextlib.suppress(KeyError):
        events.append(special_dates[date.strftime('%m-%d')])
    for birthday in process_birthdays(date, birthdays):
        events.append('{0[name]} {0[age]} jaar'.format(birthday))
    for wedding in process_weddings(date, weddings):
        events.append('{0[names]} {0[age]} jaar getrouwd'.format(wedding))
    result = dict(
        day=int(date.strftime('%d')),
        month=date.strftime('%B'),
        short_month=date.strftime('%b'),
        week_day=date.strftime('%A').capitalize(),
        events=events
    )
    log = '{0[week_day]:<10} {0[day]:>2} {0[month]}'.format(result)
    if events:
        log += ' ({})'.format(', '.join(events)).replace('\n', ': ')
    print(log)
    return result


def create_week(start_date, birthdays, weddings, special_dates):
    """
    Generate a dictionary representing an entire week.

    Args:
        start_date (datetime.date): The first day of the week to render.
        birthdays (dict): A dict of dates mapped to birthdays.
        weddings (dict): A dict of dates mapped to wedding dates.
        special_dates (dict): A dict mapping a date in the form '%m-%d'
            to a special string to render.

    Returns:
        dict: A dict containing all days of the weeks, the weeknumber
            and the month as a string.

    """
    week_number = start_date.isocalendar()[1]
    print('\n    Week {: <2d}'.format(week_number))
    args = birthdays, weddings, special_dates
    week = dict(
        weeknumber=week_number,
        mon=day_to_dict(start_date, *args),
        tue=day_to_dict(start_date + datetime.timedelta(days=1), *args),
        wed=day_to_dict(start_date + datetime.timedelta(days=2), *args),
        thu=day_to_dict(start_date + datetime.timedelta(days=3), *args),
        fri=day_to_dict(start_date + datetime.timedelta(days=4), *args),
        sat=day_to_dict(start_date + datetime.timedelta(days=5), *args),
        sun=day_to_dict(start_date + datetime.timedelta(days=6), *args),
    )
    first_month = week['sun']['month'].capitalize()
    last_month = week['mon']['month'].capitalize()
    if first_month == last_month:
        week['month'] = first_month
    else:
        week['month'] = '{} / {}'.format(first_month, last_month)
    return week


def create_weeks_for_year(year, birthdays, weddings, special_dates):
    """
    Generate all week data for a year

    Args:
        year (int): The year to generate week data for.
        birthdays (dict): A dict of dates mapped to birthdays.
        weddings (dict): A dict of dates mapped to wedding dates.
        special_dates (dict): A dict mapping a date in the form '%m-%d'
            to a special string to render.

    Yields:
        dict: All weeks for a year generated using :func:`.create_week`.

    """
    first_date = start_date(year)
    while first_date.year <= year:
        yield create_week(first_date, birthdays, weddings, special_dates)
        first_date += datetime.timedelta(days=7)


def generate(template_path, data_file, out_file=None, year=None):
    """
    Generate a week calendar for an entire year in odt format.

    Args:
        template_path (str): The file path of the template to render.
        data_file (str): The path of the configuration to load.
        out_file (io.IOBase): A file-like object to write the calendar
            to.
        year (int): The year to render the calendar for. A year
            specified in the data_file is used as a fallback value.

    Raises:
        .BadConfigError: If the given configuration file is missing
            configurations.

    """
    with open(data_file) as f:
        calendar_data = yaml.load(f)
    try:
        year = year or calendar_data['year']
        birthdays = calendar_data['birthdays']
        weddings = calendar_data['weddings']
        special_dates = calendar_data['special dates']
    except KeyError:
        raise BadConfigError()
    weeks = create_weeks_for_year(year, birthdays, weddings, special_dates)
    template = Template(source=None, filepath=template_path)
    generated = template.generate(weeks=weeks)
    data = generated.render().getvalue()
    if not out_file:
        out_file = open('calendar-{:d}.odt'.format(year), 'wb')
    out_file.write(data)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'config',
        help='The config file to use.')
    parser.add_argument(
        '-y', '--year',
        type=int,
        help='The year to render the calendar for.'
             ' (default: year specified in config file)')
    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('wb'),
        help='The output file to write the calendar to.'
             ' (default: calendar-{year}.odt)')
    args = parser.parse_args()
    locale.setlocale(locale.LC_TIME, 'nl_NL.utf8')
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'template.odt')
        generate(template_path, args.config, args.output, args.year)
    except BadConfigError:
        parser.print_help()


if __name__ == '__main__':
    main()
