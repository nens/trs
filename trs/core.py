# Calculation core around the models.
import datetime
import logging
import time

from django.core.cache import cache
from django.db import models
from django.utils.functional import cached_property

from trs.models import YearWeek
from trs.models import Booking
from trs.models import WorkAssignment

logger = logging.getLogger(__name__)

ALL = 'ALL'


class PersonYearCombination(object):
    PYC_KEYS = [
        'target',
        'turnover',
        'overbooked',
        'left_to_book',
        'well_booked',
        'booked_internal',
        'booked_external',
        'overbooked_percentage',
        'well_booked_percentage',
        'billable_percentage',
        'unbillable_percentage',
        'per_project',
    ]

    def __init__(self, person, year=None):
        self.person = person
        if year is None:
            year = datetime.date.today().year
        self.year = year
        version = 17
        self.cache_key = 'pycdata-%s-%s-%s-%s' % (
            person.id, person.cache_indicator, year, version)
        has_cached_data = self.get_cache()
        if not has_cached_data:
            self.just_calculate_everything()
            self.set_cache()

    def just_calculate_everything(self):
        start_time = time.time()
        last_year_week = YearWeek.objects.filter(year=self.year).last()
        self.target = self.person.target(year_week=last_year_week)
        self.calc_target_and_overbookings()
        self.billable_percentage = self.calc_external_percentage()
        self.unbillable_percentage = 100 - self.billable_percentage
        elapsed = (time.time() - start_time)
        logger.debug("Re-calculated person/year info for %s in % secs",
                     self.person, elapsed)

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
        budget_per_project = WorkAssignment.objects.filter(
            assigned_to=self.person,
            year_week__year__lte=self.year,
            assigned_on__start__year__lte=self.year,
            assigned_on__end__year__gte=self.year,
            assigned_on__hourless=False).values(
                'assigned_on',
                'assigned_on__internal').annotate(
                    models.Sum('hours'),
                    models.Sum('hourly_tariff')
                )
        budget = {
            item['assigned_on']: round(item['hours__sum'] or 0)
            for item in budget_per_project}
        hourly_tariff = {
            item['assigned_on']: round(item['hourly_tariff__sum'] or 0)
            for item in budget_per_project}
        is_internal = {
            item['assigned_on']: item['assigned_on__internal']
            for item in budget_per_project}

        project_ids = budget.keys()

        booked_this_year_per_project = Booking.objects.filter(
            booked_by=self.person,
            year_week__year=self.year,
            booked_on__hourless=False).values(
                'booked_on').annotate(
                    models.Sum('hours'))
        booked_this_year = {
            item['booked_on']: round(item['hours__sum'])
            for item in booked_this_year_per_project}

        booked_up_to_this_year_per_project = Booking.objects.filter(
            booked_by=self.person,
            year_week__year__lt=self.year,
            booked_on__in=project_ids).values(
                'booked_on').annotate(
                    models.Sum('hours'))
        booked_before_this_year = {
            item['booked_on']: round(item['hours__sum'])
            for item in booked_up_to_this_year_per_project}

        per_project = {}
        for id in project_ids:
            booked = booked_this_year.get(id, 0)
            booked_till_now = booked + booked_before_this_year.get(id, 0)
            overbooked = max(0, (booked_till_now - budget[id]))
            overbooked_this_year = min(overbooked, booked_this_year.get(id, 0))
            well_booked_this_year = booked_this_year.get(id, 0) - overbooked_this_year
            turnover = well_booked_this_year * hourly_tariff[id]
            left_to_book = max(0, (budget[id] - booked_till_now))
            if is_internal[id]:
                booked_internal = booked_this_year.get(id, 0)
                booked_external = 0
            else:
                booked_internal = 0
                booked_external = booked_this_year.get(id, 0)

            project_info = {
                'booked': booked,
                'overbooked': overbooked_this_year,
                'well_booked': well_booked_this_year,
                'left_to_book': left_to_book,
                'turnover': turnover,
                'booked_internal': booked_internal,
                'booked_external': booked_external,
            }
            per_project[id] = project_info

        self.overbooked = sum([project['overbooked']
                               for project in per_project.values()])
        self.well_booked = sum([project['well_booked']
                                for project in per_project.values()])
        self.turnover = sum([project['turnover']
                             for project in per_project.values()])
        self.left_to_book = sum([project['left_to_book']
                                 for project in per_project.values()])
        self.booked_internal = sum([project['booked_internal']
                                    for project in per_project.values()])
        self.booked_external = sum([project['booked_external']
                                    for project in per_project.values()])
        total_booked = sum([project['booked']
                            for project in per_project.values()])
        if total_booked:
            overbooked_percentage = round(
                100 * self.overbooked / total_booked)
            well_booked_percentage = 100 - overbooked_percentage
        else:
            overbooked_percentage = 0
            well_booked_percentage = 100

        self.overbooked_percentage = overbooked_percentage
        self.well_booked_percentage = well_booked_percentage
        self.per_project = per_project

    def calc_external_percentage(self):
        """Return percentage hours booked this year on external projects.
        """
        query_result = Booking.objects.filter(
            booked_by=self.person,
            booked_on__hourless=False,
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
            return 100
        return round(100 * external / (internal + external))

    @cached_property
    def target_percentage(self):
        if not self.target:  # Division by zero.
            return 100
        return round(self.turnover / self.target * 100)

    @cached_property
    def left_to_turn_over(self):
        return max((self.target - self.turnover), 0)


def get_pyc(person, year=None):
    return PersonYearCombination(person, year)
