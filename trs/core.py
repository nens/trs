# Calculation core around the models.
from django.db import models


class ProjectPersonCombination(object):

    def __init__(self, project, person):
        self.project = project
        self.person = person

    @property
    def budget(self):
        return self.person.work_assignments.filter(
            assigned_on=self.project).aggregate(
                models.Sum('hours'))['hours__sum'] or 0

    @property
    def booked(self):
        return self.person.bookings.filter(
            booked_on=self.project).aggregate(
                models.Sum('hours'))['hours__sum'] or 0

    @property
    def is_overbooked(self):
        return (self.booked > self.budget)

    @property
    def financially_booked(self):
        """Return booked hours, but limit it to the budget.

        You don't earn extra money by going over your hour budget.
        """
        if self.is_overbooked:
            return self.budget
        return self.booked

    @property
    def left_to_book(self):
        return self.budget - self.financially_booked

    @property
    def turnover(self):
        return self.financially_booked * self.hourly_tariff

    @property
    def left_to_turn_over(self):
        return self.left_to_book * self.hourly_tariff

    @property
    def hourly_tariff(self):
        return self.person.work_assignments.filter(
            assigned_on=self.project).aggregate(
                models.Sum('hourly_tariff'))['hourly_tariff__sum'] or 0

    @property
    def is_project_leader(self):
        return (self.person == self.project.project_leader)

    @property
    def is_project_manager(self):
        return (self.person == self.project.project_manager)
