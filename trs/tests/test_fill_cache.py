import unittest  # Note: this is 3.3's unittest2!

import pytest
from django.core.cache import cache

from trs.management.commands import fill_cache
from trs.management.commands.update_weeks import ensure_year_weeks_are_present
from trs.tests import factories


@pytest.mark.django_db
class TestFillCache(unittest.TestCase):
    def setUp(self):
        self.command = fill_cache.Command()

    def test_handle(self):
        ensure_year_weeks_are_present()
        self.person = factories.PersonFactory.create()
        self.project = factories.ProjectFactory.create()
        self.command.handle()
        key = self.project.cache_key("work_calculation")
        self.assertTrue(cache.get(key))
