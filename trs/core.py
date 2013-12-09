# Calculation core around the models.
import datetime
import logging

from django.core.cache import cache
from django.db import models
from django.utils.functional import cached_property

from trs.models import YearWeek

logger = logging.getLogger(__name__)

ALL = 'ALL'


class ProjectPersonCombination(object):
    PPC_KEYS = ['is_project_leader',
                'is_project_manager',
                'budget',
                'booking_table',
                'booked',
                'hourly_tariff',
                'desired_hourly_tariff',
                ]

    def __init__(self, project, person):
        self.project = project
        self.person = person
        self.cache_key = 'ppcdata-%s-REV%s-%s-REV%s' % (
            self.project.id, self.project.cache_indicator,
            self.person.id, self.person.cache_indicator)
        has_cached_data = self.get_cache()
        if not has_cached_data:
            self.just_calculate_everything()
            self.set_cache()

    def just_calculate_everything(self):
        # logger.debug("Calculating everything")
        self.is_project_leader = (self.person == self.project.project_leader)
        self.is_project_manager = (self.person == self.project.project_manager)
        self.budget = self.person.work_assignments.filter(
            assigned_on=self.project).aggregate(
                models.Sum('hours'))['hours__sum'] or 0
        self.booking_table = self._booking_table()
        self.booked = self.person.bookings.filter(
            booked_on=self.project).aggregate(
                models.Sum('hours'))['hours__sum'] or 0
        self.hourly_tariff = self.person.work_assignments.filter(
            assigned_on=self.project).aggregate(
                models.Sum('hourly_tariff'))['hourly_tariff__sum'] or 0
        self.desired_hourly_tariff = self.person.standard_hourly_tariff(
            year_week=self.project.start)

    def set_cache(self):
        result = {key: getattr(self, key) for key in self.PPC_KEYS}
        cache.set(self.cache_key, result)
        logger.debug("Cached NEW ppc data for %s & %s, %s",
                     self.project, self.person, self.cache_key)

    def get_cache(self):
        result = cache.get(self.cache_key)
        if not result:
            return False
        for key in self.PPC_KEYS:
            setattr(self, key, result[key])
        return True

    def _booking_table(self):
        logger.info("Starting creating booking table for %s & %s",
                    self.project, self.person)
        phase1 = self.person.bookings.filter(booked_on=self.project).values(
            'year_week__year', 'year_week__week', 'booked_on__internal').annotate(
                hours=models.Sum('hours'))
        hours_left = self.budget
        result = []
        for week_result in phase1:
            year = week_result['year_week__year']
            week = week_result['year_week__week']
            hours = week_result['hours']
            internal = week_result['booked_on__internal']
            if hours > hours_left:
                booked = hours_left
                overbooked = hours - hours_left
            else:
                booked = hours
                overbooked = 0
            hours_left -= booked
            result.append(dict(year=year,
                               week=week,
                               booked=booked,
                               overbooked=overbooked,
                               internal=internal))
        logger.info("Finished creating booking table for %s", self.project)
        return result

    @cached_property
    def is_overbooked(self):
        return (self.booked > self.budget)

    @cached_property
    def financially_booked(self):
        """Return booked hours, but limit it to the budget.

        You don't earn extra money by going over your hour budget.
        """
        if self.is_overbooked:
            return self.budget
        return self.booked

    @cached_property
    def left_to_book(self):
        return self.budget - self.financially_booked

    @cached_property
    def turnover(self):
        return self.financially_booked * self.hourly_tariff

    @cached_property
    def loss(self):
        if not self.is_overbooked:
            return 0
        return self.hourly_tariff * (self.booked - self.budget)

    @cached_property
    def left_to_turn_over(self):
        return self.left_to_book * self.hourly_tariff


class PersonYearCombination(object):
    PYC_KEYS = [
        'first_year_week',
        'last_year_week',
        'target',
        'turnover',
        'overbooked',
        'billable_percentage',
        ]

    def __init__(self, person, year=None):
        self.person = person
        if year is None:
            year = datetime.date.today().year
        self.year = year
        self.cache_key = 'pycdata-%s-%s-%s' % (person.id, person.cache_indicator, year)
        has_cached_data = self.get_cache()
        if not has_cached_data:
            self.just_calculate_everything()
            self.set_cache()

    def just_calculate_everything(self):
        self.first_year_week = YearWeek.objects.filter(year=self.year)[0]
        self.last_year_week = YearWeek.objects.filter(year=self.year).last()
        self.target = self.person.target(year_week=self.last_year_week)
        self.turnover = self._turnover()
        self.overbooked = self._overbooked()
        self.billable_percentage = self._billable_percentage()

    def set_cache(self):
        result = {key: getattr(self, key) for key in self.PYC_KEYS}
        cache.set(self.cache_key, result)
        logger.debug("Cached NEW pyc data for %s (%s) , %s",
                     self.person, self.year, self.cache_key)

    def get_cache(self):
        result = cache.get(self.cache_key)
        if not result:
            return False
        for key in self.PYC_KEYS:
            setattr(self, key, result[key])
        return True

    @cached_property
    def ppcs(self):
        # return [ProjectPersonCombination(project, self.person)
        #         for project in self.person.assigned_projects()]
        return [get_ppc(project, self.person)
                for project in self.person.assigned_projects()]

    def _turnover(self):
        result = 0
        for ppc in self.ppcs:
            booked_billable = sum(
                [info['booked'] for info in ppc.booking_table
                 if info['year'] == self.year and not info['internal']])
            result += booked_billable * ppc.hourly_tariff
        return result

    @cached_property
    def target_percentage(self):
        if not self.target:  # Division by zero.
            return 100
        return round(self.turnover / self.target * 100)

    @cached_property
    def left_to_turn_over(self):
        return max((self.target - self.turnover), 0)

    def _overbooked(self):
        result = {'over': 0, 'percentage': 0}
        well_booked = 0
        for ppc in self.ppcs:
            result['over'] += sum(
                [info['overbooked'] for info in ppc.booking_table
                 if info['year'] == self.year and not info['internal']])
            well_booked += sum(
                [info['booked'] for info in ppc.booking_table
                 if info['year'] == self.year and not info['internal']])
        if (well_booked + result['over']):
            result['percentage'] = round(
                result['over'] / (well_booked + result['over']) * 100)
        return result

    def _billable_percentage(self):
        # Count both booked and overbooked hours.
        # TODO: filter out holidays?
        billable = 0
        unbillable = 0
        for ppc in self.ppcs:
            billable += sum(
                [info['booked'] + info['overbooked']
                 for info in ppc.booking_table
                 if info['year'] == self.year and not info['internal']])
            unbillable += sum(
                [info['booked'] + info['overbooked']
                 for info in ppc.booking_table
                 if info['year'] == self.year and info['internal']])
        if not (billable + unbillable):  # Division by zero
            return 0
        return round(billable / (billable + unbillable) * 100)


def get_ppc(project, person):
    return ProjectPersonCombination(project, person)


def get_pyc(person, year=None):
    cache_key = 'pyc-%s-%s-%s' % (person.id, person.cache_indicator, year)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = PersonYearCombination(person, year)
    cache.set(cache_key, result)
    return result
