# import unittest  # Note: this is 3.3's unittest2!

from django.test import TestCase

from trs import models


class PersonTestCase(TestCase):

    def test_smoke(self):
        person = models.Person()
        person.save()
        self.assertTrue(person)

    def test_representation(self):
        person = models.Person(name='Reinout')
        self.assertEqual(str(person), 'Person Reinout')


class ProjectTestCase(TestCase):

    def test_smoke(self):
        project = models.Project()
        project.save()
        self.assertTrue(project)

    def test_representation(self):
        project = models.Project(code='P1234')
        self.assertEqual(str(project), 'Project P1234')
