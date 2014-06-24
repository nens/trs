from django.core.cache import cache
from django.test import TestCase
import mock

from trs import models
from trs import core
from trs.tests import factories
from trs.management.commands.update_weeks import ensure_year_weeks_are_present


class PersonYearCombinationTestCase(TestCase):

    def setUp(self):
        ensure_year_weeks_are_present()
        self.person = factories.PersonFactory.create()
        self.project1 = factories.ProjectFactory.create()
        self.project2 = factories.ProjectFactory.create()
        self.project3 = factories.ProjectFactory.create(internal=True)
        factories.WorkAssignmentFactory(
            assigned_to=self.person,
            assigned_on=self.project1,
            hours=10,
            hourly_tariff=10)
        factories.WorkAssignmentFactory(
            assigned_to=self.person,
            assigned_on=self.project2,
            hours=20,
            hourly_tariff=20)
        factories.WorkAssignmentFactory(
            assigned_to=self.person,
            assigned_on=self.project3,
            hours=30,
            hourly_tariff=30)
        factories.BookingFactory(
            booked_by=self.person,
            booked_on=self.project1)
        self.pyc = core.PersonYearCombination(self.person)
        # Bust the cache explicitly
        cache.set(self.pyc.cache_key, None)

    def test_smoke(self):
        self.assertEqual(self.pyc.person, self.person)

    def test_cache_works(self):
        cache.set('my_cache_key', 42)
        self.assertEqual(cache.get('my_cache_key'), 42)

    def test_empty_cache(self):
        self.assertFalse(self.pyc.get_cache())

    def test_full_cache(self):
        self.pyc.set_cache()
        self.assertTrue(self.pyc.get_cache())
