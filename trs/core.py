# Calculation core around the models.
from django.db import models


class ProjectPersonCombination(object):

    def __init__(self, project, person, request=None):
        self.project = project
        self.person = person
        self.request = request

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
    def overbooked(self):
        return (self.booked > self.budget)

    @property
    def financially_booked(self):
        """Return booked hours, but limit it to the budget.

        You don't earn extra money by going over your hour budget.
        """
        if self.overbooked:
            return self.budget
        return self.booked

    @property
    def left_to_book(self):
        return self.budget - self.financially_booked
