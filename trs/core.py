# Calculation core around the models.
import datetime
import logging

from django.core.cache import cache
from django.db import models
from django.utils.functional import cached_property

from trs.models import YearWeek
from trs.models import Booking
from trs.models import WorkAssignment
from trs.models import Project

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
        'target',
        'turnover',
        'overbooked',
        'left_to_book',
        'overbooked_percentage',
        'well_booked_percentage',
        'billable_percentage',
        'unbillable_percentage',
        ]

    def __init__(self, person, year=None):
        self.person = person
        if year is None:
            year = datetime.date.today().year
        self.year = year
        self.cache_key = 'pycdata6-%s-%s-%s' % (person.id, person.cache_indicator, year)
        has_cached_data = self.get_cache()
        if not has_cached_data:
            self.just_calculate_everything()
            self.set_cache()

    def just_calculate_everything(self):
        last_year_week = YearWeek.objects.filter(year=self.year).last()
        self.target = self.person.target(year_week=last_year_week)
        self.calc_target_and_overbookings()
        self.billable_percentage = self.calc_external_percentage()
        self.unbillable_percentage = 100 - self.billable_percentage
        logger.debug("Re-calculated person/year info for %s", self.person)

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

    def calc_target_and_overbookings(self):
        booked_this_year_per_project = Booking.objects.filter(
            booked_by=self.person,
            year_week__year=self.year,
            booked_on__internal=False).values(
                'booked_on').annotate(
                    models.Sum('hours'))
        booked_this_year = {
            item['booked_on']: round(item['hours__sum'])
            for item in booked_this_year_per_project}

        booked_up_to_this_year_per_project = Booking.objects.filter(
            booked_by=self.person,
            year_week__year__lt=self.year,
            booked_on__in=booked_this_year.keys()).values(
                'booked_on').annotate(
                    models.Sum('hours'))
        booked_before_this_year = {
            item['booked_on']: round(item['hours__sum'])
            for item in booked_up_to_this_year_per_project}

        budget_per_project = WorkAssignment.objects.filter(
            assigned_to=self.person,
            year_week__year__lte=self.year,
            assigned_on__in=booked_this_year.keys()).values(
                'assigned_on').annotate(
                    models.Sum('hours'),
                    models.Sum('hourly_tariff')
                )
        budget = {
            item['assigned_on']: round(item['hours__sum'])
            for item in budget_per_project}
        hourly_tariff = {
            item['assigned_on']: round(item['hourly_tariff__sum'])
            for item in budget_per_project}
        total_booked = 0
        total_overbooked = 0
        total_turnover = 0
        total_left_to_book = 0
        for id in booked_this_year:
            booked = booked_this_year[id] + booked_before_this_year.get(id, 0)
            total_booked += booked
            overbooked = max(0, (booked - budget[id]))
            overbooked_this_year = min(overbooked, booked_this_year[id])
            well_booked_this_year = booked_this_year[id] - overbooked_this_year
            total_overbooked += overbooked_this_year
            total_turnover += well_booked_this_year * hourly_tariff[id]
            total_left_to_book += max(0, (budget[id] - booked))

        if total_booked:
            overbooked_percentage = round(100 * total_overbooked / total_booked)
            well_booked_percentage = 100 - overbooked_percentage
        else:
            overbooked_percentage = 0
            well_booked_percentage = 0

        self.overbooked = total_overbooked
        self.overbooked_percentage = overbooked_percentage
        self.well_booked_percentage = well_booked_percentage
        self.turnover = total_turnover
        self.left_to_book = total_left_to_book

    def calc_external_percentage(self):
        """Return percentage hours booked this year on external projects.

        TODO: filter out holiday hours?
        """
        query_result = Booking.objects.filter(
            booked_by=self.person,
            year_week__year=self.year).values(
                'booked_on__internal').annotate(
                    models.Sum('hours'))
        internal = 0
        external = 0
        for result in query_result:
            if result['booked_on__internal']:
                internal = round(result['hours__sum'])
            else:
                external = round(result['hours__sum'])
        if not internal + external:  # Division by zero
            return 0
        return round(100 * external / (internal + external))

    @cached_property
    def target_percentage(self):
        if not self.target:  # Division by zero.
            return 100
        return round(self.turnover / self.target * 100)

    @cached_property
    def left_to_turn_over(self):
        return max((self.target - self.turnover), 0)


def get_ppc(project, person):
    return ProjectPersonCombination(project, person)


def get_pyc(person, year=None):
    return PersonYearCombination(person, year)
