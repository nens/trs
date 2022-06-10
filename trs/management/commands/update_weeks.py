# -*- coding: utf-8 -*-
# Copyright 2013 Nelen & Schuurmans
from django.conf import settings
from django.core.management.base import BaseCommand
from trs import models

import calendar
import datetime
import logging


logger = logging.getLogger(__name__)

MONTH_NUMBERS = range(1, 13)


def fix_num_days():
    for year in range(settings.TRS_START_YEAR, settings.TRS_END_YEAR + 1):
        first_year_week = models.YearWeek.objects.filter(year=year).first()
        missing_at_start = first_year_week.first_day.weekday()
        # .weekday() returns Mon=0, Tue=1, Wed=3.
        first_year_week.num_days_missing = missing_at_start
        first_year_week.save()

        last_year_week = models.YearWeek.objects.filter(year=year).last()
        last_day = datetime.date(year=year, month=12, day=31)
        missing_at_end = max(0, 4 - last_day.weekday())
        last_year_week.num_days_missing = missing_at_end
        last_year_week.save()


def year_and_week_from_date(date):
    """Return year and week (as string).

    Adjustment to the normal ISO rules
    (http://www.staff.science.uu.nl/~gent0113/calendar/isocalendar.htm): The
    first or last days of the year can be in a week that belongs to the next
    or previous year. We adjust this so that the year always matches, using
    week 53 and week 0 when necessary."""
    year, week, weekday = date.isocalendar()
    if year < date.year:
        # First part of january can still belong to the previous year. Adjust
        # to week zero.
        year = date.year
        week = 0
    if year > date.year:
        # End part of december can already belong to the next year. Adjust to
        # week 53.
        year = date.year
        week = 53
    return year, week


def interesting_days(year):
    """Return all mondays and 1 january."""
    cal = calendar.Calendar()
    days = []
    for month_number in MONTH_NUMBERS:
        for week in cal.monthdayscalendar(year, month_number):
            if week[0]:
                days.append(datetime.date(year, month_number, week[0]))
    first_of_january = datetime.date(year, 1, 1)
    third_of_january = datetime.date(year, 1, 3)
    # ^^ Allow for sat+sun before.
    if days[0] > third_of_january:
        # Prepend 1 january.
        days[0:0] = [first_of_january]
    return days


def ensure_year_weeks_are_present():
    count = 0
    for year in range(settings.TRS_START_YEAR, settings.TRS_END_YEAR + 1):
        for date in interesting_days(year):
            year, week = year_and_week_from_date(date)
            obj, added = models.YearWeek.objects.get_or_create(
                year=year, week=week, first_day=date
            )
            if added:
                count += 1
    logger.info("Added %s YearWeek objects", count)
    fix_num_days()
    logger.info("Adjusted the number of days per week where necessary.")


class Command(BaseCommand):
    args = ""
    help = "Add the necessary year/week objects to the database."

    def handle(self, *args, **options):
        ensure_year_weeks_are_present()
