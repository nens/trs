# import unittest  # Note: this is 3.3's unittest2!
from django.test import TestCase
from django.core.exceptions import ValidationError

from trs import models


class PersonTestCase(TestCase):

    def test_smoke(self):
        person = models.Person()
        person.save()
        self.assertTrue(person)

    def test_representation(self):
        person = models.Person(name='Reinout')
        self.assertEqual(str(person), 'Person Reinout')

    def test_get_absolute_url(self):
        person = models.Person(name='Reinout', slug='reinout')
        self.assertEqual(person.get_absolute_url(), '/persons/reinout/')

    def test_as_widget(self):
        person = models.Person(name='Reinout', slug='reinout')
        self.assertTrue(person.as_widget())

    def test_sorting(self):
        person1 = models.Person(name='Reinout')
        person1.save()
        person2 = models.Person(name='Maurits')
        person2.save()
        self.assertEqual(models.Person.objects.all()[0].name,
                         'Maurits')


class ProjectTestCase(TestCase):

    def test_smoke(self):
        project = models.Project()
        project.save()
        self.assertTrue(project)

    def test_representation(self):
        project = models.Project(code='P1234')
        self.assertEqual(str(project), 'Project P1234')

    def test_get_absolute_url(self):
        project = models.Project(code='P1234', slug='P1234')
        self.assertEqual(project.get_absolute_url(), '/projects/P1234/')

    def test_as_widget(self):
        project = models.Project(code='P1234', slug='P1234')
        self.assertTrue(project.as_widget())

    def test_sorting(self):
        project1 = models.Project(code='P1234')
        project1.save()
        project2 = models.Project(code='P0123')
        project2.save()
        self.assertEqual(models.Project.objects.all()[0].code,
                         'P0123')


class PersonChangeTestCase(TestCase):

    def test_smoke(self):
        person_change = models.PersonChange(year_and_week='1972-51')
        person_change.save()
        self.assertTrue(person_change)


class BookingTestCase(TestCase):

    def test_smoke(self):
        booking = models.Booking(year_and_week='1972-51')
        booking.save()
        self.assertTrue(booking)


class WorkAssignmentTestCase(TestCase):

    def test_smoke(self):
        work_assignment = models.WorkAssignment(year_and_week='1972-51')
        work_assignment.save()
        self.assertTrue(work_assignment)


class BudgetAssignmentTestCase(TestCase):

    def test_smoke(self):
        budget_assignment = models.BudgetAssignment(year_and_week='1972-51')
        budget_assignment.save()
        self.assertTrue(budget_assignment)


class YearWeekValidatorTestCase(TestCase):

    def test_correct1(self):
        value = '1972-51'
        self.assertEqual(models.is_year_and_week_format(value), None)

    def test_correct2(self):
        value = '1972-00'
        self.assertEqual(models.is_year_and_week_format(value), None)

    def test_correct3(self):
        value = '1972-53'
        self.assertEqual(models.is_year_and_week_format(value), None)

    def test_faulty_format1(self):
        value = '1972_51'
        with self.assertRaises(ValidationError):
            models.is_year_and_week_format(value)

    def test_faulty_format2(self):
        value = '72_51'
        with self.assertRaises(ValidationError):
            models.is_year_and_week_format(value)

    def test_faulty_format3(self):
        value = '1972-54'
        with self.assertRaises(ValidationError):
            models.is_year_and_week_format(value)

    def test_faulty_format4(self):
        value = '197251'
        with self.assertRaises(ValidationError):
            models.is_year_and_week_format(value)
