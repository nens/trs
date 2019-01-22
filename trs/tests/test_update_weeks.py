import unittest  # Note: this is 3.3's unittest2!
import datetime

from trs.management.commands import update_weeks
from trs import models


class TestUpdateWeeks(unittest.TestCase):
    def setUp(self):
        self.command = update_weeks.Command()

    def test_interesting_days1(self):
        # 1 jan 2007 was a monday, so 2007 should be just the mondays.
        # 31 dec 2007 is also a monday, so there are 53 interesting days.
        result = update_weeks.interesting_days(2007)
        self.assertEqual(len(result), 53)
        self.assertEqual(result[0], datetime.date(2007, 1, 1))
        self.assertEqual(result[52], datetime.date(2007, 12, 31))

    def test_interesting_days2(self):
        # 1 jan 2013 was a tuesday.
        # 7 jan was the first monday.
        # 30 december is the last monday.
        result = update_weeks.interesting_days(2013)
        self.assertEqual(result[0], datetime.date(2013, 1, 1))
        self.assertEqual(result[1], datetime.date(2013, 1, 7))
        self.assertEqual(result[52], datetime.date(2013, 12, 30))

    def test_interesting_days3(self):
        # 1 jan 2011 was a saturday.
        # 3 jan was the first monday.
        # We're not interested in 1&2 jan, as there would be no working days
        # in that zero-numbered week!
        result = update_weeks.interesting_days(2011)
        self.assertEqual(result[0], datetime.date(2011, 1, 3))

    def test_week_from_date1(self):
        d = datetime.date(2013, 10, 7)
        self.assertEqual(update_weeks.year_and_week_from_date(d), (2013, 41))

    def test_week_from_date2(self):
        d = datetime.date(2010, 1, 1)
        # A friday in week 53 of 2009! Should become week 0 of 2010
        self.assertEqual(update_weeks.year_and_week_from_date(d), (2010, 0))

    def test_week_from_date3(self):
        d = datetime.date(2012, 12, 31)
        # A monday in week 1 of 2013! Should become week 53 of 2012
        self.assertEqual(update_weeks.year_and_week_from_date(d), (2012, 53))

    def test_handle(self):
        self.command.handle()
        year_week = models.YearWeek.objects.get(year=2012, week=53)
        self.assertEqual(year_week.first_day, datetime.date(2012, 12, 31))
