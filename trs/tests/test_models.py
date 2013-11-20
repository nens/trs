# import unittest  # Note: this is 3.3's unittest2!
from django.test import TestCase

from trs import models
from trs.tests import factories


class PersonTestCase(TestCase):

    def test_smoke(self):
        person = factories.PersonFactory.create()
        self.assertTrue(person)

    def test_representation(self):
        person = factories.PersonFactory.build(name='Pietje')
        self.assertEqual(str(person), 'Pietje')

    def test_get_absolute_url(self):
        person = factories.PersonFactory.build(slug='reinout')
        self.assertEqual(person.get_absolute_url(), '/persons/reinout/')

    def test_as_widget(self):
        person = factories.PersonFactory.build()
        self.assertTrue(person.as_widget())

    def test_sorting(self):
        factories.PersonFactory.create(name='Reinout')
        factories.PersonFactory.create(name='Maurits')
        self.assertEqual(models.Person.objects.all()[0].name,
                         'Maurits')

    def test_hours_per_week1(self):
        factories.YearWeekFactory.create()  # We need one for the query.
        person = factories.PersonFactory.create()
        self.assertEqual(person.hours_per_week(), 0)

    def test_hours_per_week2(self):
        person = factories.PersonFactory.create()
        factories.PersonChangeFactory.create(hours_per_week=40, person=person)
        self.assertEqual(person.hours_per_week(), 40)

    def test_hours_per_week3(self):
        person = factories.PersonFactory.create()
        factories.PersonChangeFactory.create(hours_per_week=40, person=person)
        factories.PersonChangeFactory.create(hours_per_week=-2, person=person)
        self.assertEqual(person.hours_per_week(), 38)

    def test_target1(self):
        factories.YearWeekFactory.create()  # We need one for the query.
        person = factories.PersonFactory.create()
        self.assertEqual(person.target(), 0)

    def test_target2(self):
        person = factories.PersonFactory.create()
        factories.PersonChangeFactory.create(target=10000, person=person)
        self.assertEqual(person.target(), 10000)

    def test_target3(self):
        person = factories.PersonFactory.create()
        factories.PersonChangeFactory.create(target=10000, person=person)
        factories.PersonChangeFactory.create(target=-1000, person=person)
        self.assertEqual(person.target(), 9000)

    def test_assigned_projects1(self):
        person = factories.PersonFactory.create()
        self.assertEqual(len(person.assigned_projects()), 0)

    def test_assigned_projects2(self):
        person = factories.PersonFactory.create()
        project = factories.ProjectFactory.create()
        factories.WorkAssignmentFactory(assigned_to=person,
                                        assigned_on=project)
        self.assertEqual(person.assigned_projects()[0], project)

    def test_booking_percentage1(self):
        person = factories.PersonFactory.create()
        self.assertEqual(person.booking_percentage(), 100)

    def test_booking_percentage2(self):
        person = factories.PersonFactory.create()
        test_weeks = [factories.YearWeekFactory.create()
                      for i in range(5)]
        factories.PersonChangeFactory.create(
            person=person,
            hours_per_week=10,
            year_week=test_weeks[0])
        # Supposed to work 10 hours, didn't do a thing.
        self.assertEqual(person.booking_percentage(), 0)

    def test_booking_percentage3(self):
        person = factories.PersonFactory.create()
        test_weeks = [factories.YearWeekFactory.create()
                      for i in range(5)]
        factories.PersonChangeFactory.create(
            person=person,
            hours_per_week=10,
            year_week=test_weeks[0])
        factories.BookingFactory(
            hours=10,
            booked_by=person,
            year_week=test_weeks[2])
        # Supposed to work 4*10 hours, worked 10, so 25%.
        self.assertEqual(person.booking_percentage(), 25)


class ProjectTestCase(TestCase):

    def test_smoke(self):
        project = factories.ProjectFactory.create()
        self.assertTrue(project)

    def test_representation(self):
        project = factories.ProjectFactory.build(code='P1234')
        self.assertEqual(str(project), 'P1234')

    def test_get_absolute_url(self):
        project = factories.ProjectFactory.build(slug='p1234')
        self.assertEqual(project.get_absolute_url(), '/projects/p1234/')

    def test_as_widget(self):
        project = factories.ProjectFactory.build()
        self.assertTrue(project.as_widget())

    def test_sorting(self):
        factories.ProjectFactory.create(code='P1234')
        factories.ProjectFactory.create(code='P0123')
        self.assertEqual(models.Project.objects.all()[0].code,
                         'P0123')

    def test_assigned_persons1(self):
        project = factories.ProjectFactory.create()
        self.assertEqual(len(project.assigned_persons()), 0)

    def test_assigned_persons2(self):
        person = factories.PersonFactory.create()
        project = factories.ProjectFactory.create()
        factories.WorkAssignmentFactory(assigned_to=person,
                                        assigned_on=project)
        self.assertEqual(project.assigned_persons()[0], person)

    def test_budget1(self):
        project = factories.ProjectFactory.create()
        self.assertEqual(project.budget(), 0)

    def test_budget2(self):
        project = factories.ProjectFactory.create()
        factories.BudgetAssignmentFactory.create(
            budget=1000,
            assigned_to=project)
        self.assertEqual(project.budget(), 1000)


class YearWeekTestCase(TestCase):

    def test_smoke(self):
        year_week = factories.YearWeekFactory.create()
        self.assertTrue(year_week)

    def test_create_two_from_factory(self):
        factories.YearWeekFactory.create()
        year_week2 = factories.YearWeekFactory.create()
        self.assertTrue(year_week2)

    def test_representation(self):
        year_week = factories.YearWeekFactory.create(year=1972, week=51)
        self.assertEqual(str(year_week), '1972-51')

    def test_get_absolute_url(self):
        year_week = factories.YearWeekFactory.create(year=1972, week=51)
        self.assertEqual(year_week.get_absolute_url(), '/booking/1972-51/')

    def test_as_widget(self):
        year_week = factories.YearWeekFactory.create()
        self.assertTrue(year_week.as_widget())

    def test_friendly(self):
        year_week = factories.YearWeekFactory.create()
        self.assertTrue(year_week.friendly())


class PersonChangeTestCase(TestCase):

    def test_smoke(self):
        person_change = factories.PersonChangeFactory.create()
        self.assertTrue(person_change)

    def test_str(self):
        person_change = factories.PersonChangeFactory.create()
        self.assertTrue(str(person_change))

class BookingTestCase(TestCase):

    def test_smoke(self):
        booking = factories.BookingFactory.create()
        self.assertTrue(booking)


class WorkAssignmentTestCase(TestCase):

    def test_smoke(self):
        work_assignment = factories.WorkAssignmentFactory.create()
        self.assertTrue(work_assignment)


class BudgetAssignmentTestCase(TestCase):

    def test_smoke(self):
        budget_assignment = factories.BudgetAssignmentFactory.create()
        self.assertTrue(budget_assignment)


class UtilsTestCase(TestCase):

    def setUp(self):
        self.test_weeks = [factories.YearWeekFactory.create()
                           for i in range(10)]

    def test_last_four_year_weeks1(self):
        self.assertEqual(len(models.last_four_year_weeks()), 4)

    def test_last_four_year_weeks2(self):
        self.assertEqual(list(models.last_four_year_weeks())[-1],
                         self.test_weeks[8])
