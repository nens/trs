# -*- coding: utf-8 -*-
# Copyright 2013 Nelen & Schuurmans
import calendar
import datetime
import logging

from django.core.management.base import BaseCommand
from django.conf import settings

from trs import models

logger = logging.getLogger(__name__)

MONTH_NUMBERS = range(1, 13)


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


class Command(BaseCommand):
    args = ""
    help = "Add the necessary year/week objects to the database."

    def handle(self, *args, **options):
        count = 0
        for year in range(settings.TRS_START_YEAR, settings.TRS_END_YEAR + 1):
            for date in self.interesting_days(year):
                year, week = year_and_week_from_date(date)
                obj, added = models.YearWeek.objects.get_or_create(
                    year=year,
                    week=week,
                    first_day=date)
                if added:
                    count += 1
        logger.info("Added %s YearWeek objects", count)

    def interesting_days(self, year):
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
