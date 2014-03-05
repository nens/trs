# Calculation core around the models.
import datetime
import logging
import time

from django.core.cache import cache
from django.db import models
from django.utils.functional import cached_property

from trs.models import Booking
from trs.models import Project
from trs.models import WorkAssignment
from trs.models import YearWeek

logger = logging.getLogger(__name__)

ALL = 'ALL'


class PersonYearCombination(object):
    PYC_KEYS = [
        'target',
        'turnover',
        'overbooked',
        'left_to_book_external',
        'well_booked',
        'booked_internal',
        'booked_external',
        'overbooked_percentage',
        'well_booked_percentage',
        'billable_percentage',
        'unbillable_percentage',
        'per_project',
        'all_booked_hours',
        'to_book_this_year',
        'all_bookings_percentage',
        'left_to_turn_over',
    ]

    def __init__(self, person, year=None):
        self.person = person
        if year is None:
            year = datetime.date.today().year
        self.year = year
        version = 27
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

        contract_amounts = Project.objects.filter(
            id__in=project_ids).values(
                'id', 'contract_amount', 'contract_amount_ok')
        contract_amounts = {
            item['id']: item['contract_amount'] or item['contract_amount_ok']
            for item in contract_amounts}

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
            well_booked_this_year = (
                booked_this_year.get(id, 0) - overbooked_this_year)
            tariff = hourly_tariff[id]
            if not contract_amounts[id]:
                # Don't count anything money-wise.
                tariff = 0
            turnover = well_booked_this_year * tariff
            left_to_book = max(0, (budget[id] - booked_till_now))
            left_to_turn_over = left_to_book * tariff
            if is_internal[id]:
                booked_internal = booked_this_year.get(id, 0)
                booked_external = 0
                left_to_book_external = 0
                # ^^^ TODO: later on we might want to deal with internal
                # projects that are in fact proper projects and count their
                # left-to-book hours.
            else:
                booked_internal = 0
                booked_external = booked_this_year.get(id, 0)
                left_to_book_external = left_to_book

            project_info = {
                'booked': booked,
                'overbooked': overbooked_this_year,
                'well_booked': well_booked_this_year,
                'left_to_book_external': left_to_book_external,
                'turnover': turnover,
                'left_to_turn_over': left_to_turn_over,
                'booked_internal': booked_internal,
                'booked_external': booked_external,
            }
            per_project[id] = project_info

        # year-based person.to_work_up_till_now() implementation.
        hours_per_week = round(self.person.person_changes.filter(
            year_week__year__lt=self.year).aggregate(
                models.Sum('hours_per_week'))['hours_per_week__sum'] or 0)
        changes_this_year = self.person.person_changes.filter(
            year_week__year=self.year).values(
                'year_week__week').annotate(
                    models.Sum('hours_per_week'))
        changes_per_week = {change['year_week__week']:
                            round(change['hours_per_week__sum'])
                            for change in changes_this_year}
        year_weeks = YearWeek.objects.filter(
            year=self.year).values('week', 'num_days_missing')
        week_numbers = [year_week['week'] for year_week in year_weeks]
        missing_days = sum([year_week['num_days_missing']
                            for year_week in year_weeks])
        self.to_book_this_year = 0
        for week in week_numbers:
            if week in changes_per_week:
                hours_per_week += changes_per_week[week]
            self.to_book_this_year += hours_per_week
        self.to_book_this_year -= missing_days * 8
        self.all_booked_hours = round(self.person.bookings.filter(
            year_week__year=self.year).aggregate(
                models.Sum('hours'))['hours__sum'] or 0)
        # ^^^ self.all_booked_hours *includes* the 'hourless' projects that
        # are filtered out in the rest of this calculation.
        if self.to_book_this_year:
            self.all_bookings_percentage = round(
                100 * self.all_booked_hours / self.to_book_this_year)
        else:  # Division by zero
            self.all_bookings_percentage = 0

        self.overbooked = sum([project['overbooked']
                               for project in per_project.values()])
        self.well_booked = sum([project['well_booked']
                                for project in per_project.values()])
        self.turnover = sum([project['turnover']
                             for project in per_project.values()])
        self.left_to_turn_over = sum([project['left_to_turn_over']
                                      for project in per_project.values()])
        self.left_to_book_external = sum(
            [project['left_to_book_external']
             for project in per_project.values()])
        self.booked_internal = sum([project['booked_internal']
                                    for project in per_project.values()])
        self.booked_external = sum([project['booked_external']
                                    for project in per_project.values()])
        total_booked = sum([project['booked']
                            for project in per_project.values()])
        # ^^^ total_booked excludes, like everything here, the 'hourless'
        # projects.
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
    def relative_target_percentage(self):
        """Return target percentage relative to the elapsed days."""
        if self.year == datetime.date.today().year:
            days_elapsed = datetime.date.today().timetuple().tm_yday
            portion_of_year = days_elapsed / 365
        else:
            portion_of_year = 1
        if not self.target:  # Division by zero.
            return 100
        return round(self.turnover / self.target * 100 / portion_of_year)

    @cached_property
    def relative_bar_percentage(self):
        return round(self.relative_target_percentage / 2)

    @cached_property
    def relative_bar_color(self):
        if self.relative_target_percentage >= 100:
            color = 'success'
        elif self.relative_target_percentage < 50:
            color = 'danger'
        else:
            color = 'warning'
        return 'progress-bar-' + color


def get_pyc(person, year=None):
    return PersonYearCombination(person, year)
