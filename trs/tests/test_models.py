# import unittest  # Note: this is 3.3's unittest2!
import datetime

from django.test import TestCase
import mock

from trs import models
from trs.tests import factories
from trs.management.commands.update_weeks import ensure_year_weeks_are_present


class PersonTestCase(TestCase):

    def test_smoke(self):
        person = factories.PersonFactory.create()
        self.assertTrue(person)

    def test_representation(self):
        person = factories.PersonFactory.create(name='Pietje')
        self.assertEqual(str(person), 'Pietje')

    def test_get_absolute_url(self):
        person = factories.PersonFactory.create()
        self.assertTrue(person.get_absolute_url())

    def test_as_widget(self):
        person = factories.PersonFactory.create()
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
        ensure_year_weeks_are_present()
        person = factories.PersonFactory.create()
        self.assertEqual(len(person.assigned_projects()), 0)

    def test_assigned_projects2(self):
        ensure_year_weeks_are_present()
        person = factories.PersonFactory.create()
        project = factories.ProjectFactory.create()
        factories.WorkAssignmentFactory(assigned_to=person,
                                        assigned_on=project)
        self.assertEqual(person.assigned_projects()[0], project)


class ProjectTestCase(TestCase):

    def test_smoke(self):
        project = factories.ProjectFactory.create()
        self.assertTrue(project)

    def test_representation(self):
        project = factories.ProjectFactory.create(code='P1234')
        self.assertEqual(str(project), 'P1234')

    def test_get_absolute_url(self):
        project = factories.ProjectFactory.create()
        self.assertTrue(project.get_absolute_url())

    def test_as_widget(self):
        project = factories.ProjectFactory.create()
        self.assertTrue(project.as_widget())

    def test_sorting1(self):
        factories.ProjectFactory.create(code='P1234')
        factories.ProjectFactory.create(code='P0123')
        # Newest at the top.
        self.assertEqual(models.Project.objects.all()[0].code,
                         'P1234')

    def test_sorting2(self):
        # External comes before internal.
        factories.ProjectFactory.create(code='P1234',
                                        internal=False)
        factories.ProjectFactory.create(code='P0123',
                                        internal=True)
        factories.ProjectFactory.create(code='P0001',
                                        internal=False)
        codes = [project.code for project in models.Project.objects.all()]
        self.assertEqual(codes, ['P1234', 'P0001', 'P0123'])

    def test_assigned_persons1(self):
        project = factories.ProjectFactory.create()
        self.assertEqual(len(project.assigned_persons()), 0)

    def test_assigned_persons2(self):
        person = factories.PersonFactory.create()
        project = factories.ProjectFactory.create()
        factories.WorkAssignmentFactory(assigned_to=person,
                                        assigned_on=project)
        self.assertEqual(project.assigned_persons()[0], person)


class EventBaseTestCase(TestCase):

    def test_added_by(self):
        # We use person_change as the subclass to test the abstract EventBase.
        request = mock.Mock()
        request.user = factories.UserFactory.create()
        with mock.patch('trs.models.tls_request', request):
            person_change = factories.PersonChangeFactory.create()
            self.assertEqual(person_change.added_by, request.user)


class YearWeekTestCase(TestCase):

    def test_smoke(self):
        year_week = factories.YearWeekFactory.create()
        self.assertTrue(year_week)

    def test_create_two_from_factory(self):
        factories.YearWeekFactory.create()
        year_week2 = factories.YearWeekFactory.create()
        self.assertTrue(year_week2)

    def test_representation(self):
        year_week = factories.YearWeekFactory.create(
            year=1972,
            week=51,
            first_day=datetime.date(year=1972, month=12, day=25))
        self.assertEqual(str(year_week), '25 dec 1972 (week 51)')

    def test_get_absolute_url(self):
        year_week = factories.YearWeekFactory.create(year=1972, week=51)
        self.assertEqual(year_week.get_absolute_url(), '/booking/1972-51/')

    def test_as_widget(self):
        year_week = factories.YearWeekFactory.create()
        self.assertTrue(year_week.as_widget())

    def test_friendly(self):
        year_week = factories.YearWeekFactory.create()
        self.assertTrue(year_week.friendly())

    def test_comparison(self):
        year_week1 = factories.YearWeekFactory(
            year=2014,
            week=53,
            first_day=datetime.date(year=2014, month=12, day=29))
        year_week2 = factories.YearWeekFactory(
            year=2014,
            week=27,
            first_day=datetime.date(year=2014, month=6, day=20))
        self.assertLess(year_week2, year_week1)


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


class BudgetItemTestCase(TestCase):

    def test_smoke(self):
        budget_item = factories.BudgetItemFactory.create()
        self.assertTrue(budget_item)
