# Calculation core around the models.
import datetime

from django.db import models
from django.utils.functional import cached_property

from trs.models import YearWeek

ALL = 'ALL'


class ProjectPersonCombination(object):

    def __init__(self, project, person):
        self.project = project
        self.person = person

    @cached_property
    def budget(self):
        return self.person.work_assignments.filter(
            assigned_on=self.project).aggregate(
                models.Sum('hours'))['hours__sum'] or 0

    @cached_property
    def booking_table(self):
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
        return result

    @cached_property
    def booked(self):
        return self.person.bookings.filter(
            booked_on=self.project).aggregate(
                models.Sum('hours'))['hours__sum'] or 0

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

    @cached_property
    def hourly_tariff(self):
        return self.person.work_assignments.filter(
            assigned_on=self.project).aggregate(
                models.Sum('hourly_tariff'))['hourly_tariff__sum'] or 0

    @cached_property
    def desired_hourly_tariff(self):
        """Return hourly tariff at start of project."""
        return self.person.standard_hourly_tariff(
            year_week=self.project.start)

    @cached_property
    def is_project_leader(self):
        return (self.person == self.project.project_leader)

    @cached_property
    def is_project_manager(self):
        return (self.person == self.project.project_manager)


class PersonYearCombination(object):

    def __init__(self, person, year=None):
        self.person = person
        if year is None:
            year = datetime.date.today().year
        self.year = year

    @cached_property
    def first_year_week(self):
        return YearWeek.objects.filter(year=self.year)[0]

    @cached_property
    def last_year_week(self):
        return YearWeek.objects.filter(year=self.year).last()

    @cached_property
    def target(self):
        return self.person.target(year_week=self.last_year_week)

    @cached_property
    def ppcs(self):
        return [ProjectPersonCombination(project, self.person)
                for project in self.person.assigned_projects()]

    @cached_property
    def turnover(self):
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

    @cached_property
    def overbooked(self):
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

    @cached_property
    def billable_percentage(self):
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
