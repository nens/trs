import mock
from django.test import TestCase

#from trs import models
from trs import core
from trs.tests import factories


class ProjectPersonCombinationTestCase(TestCase):

    def setUp(self):
        self.project = factories.ProjectFactory.create()
        self.person = factories.PersonFactory.create()
        self.ppc = core.ProjectPersonCombination(
            project=self.project,
            person=self.person)

    def test_smoke(self):
        self.assertTrue(self.ppc)

    def test_budget1(self):
        self.assertEqual(self.ppc.budget, 0)

    def test_budget2(self):
        factories.WorkAssignmentFactory.create(
            assigned_to=self.person,
            assigned_on=self.project,
            hours=10)
        self.assertEqual(self.ppc.budget, 10)

    def test_booked1(self):
        self.assertEqual(self.ppc.booked, 0)

    def test_booked2(self):
        factories.BookingFactory.create(
            booked_by=self.person,
            booked_on=self.project,
            hours=10)
        self.assertEqual(self.ppc.booked, 10)

    def test_is_overbooked1(self):
        self.assertEqual(self.ppc.is_overbooked, False)

    @mock.patch('trs.core.ProjectPersonCombination.booked', 10)
    def test_is_overbooked2(self):
        self.assertEqual(self.ppc.is_overbooked, True)

    @mock.patch('trs.core.ProjectPersonCombination.budget', 10)
    def test_is_overbooked3(self):
        self.assertEqual(self.ppc.is_overbooked, False)

    @mock.patch('trs.core.ProjectPersonCombination.budget', 10)
    @mock.patch('trs.core.ProjectPersonCombination.booked', 8)
    def test_financially_booked1(self):
        self.assertEqual(self.ppc.financially_booked, 8)

    @mock.patch('trs.core.ProjectPersonCombination.budget', 10)
    @mock.patch('trs.core.ProjectPersonCombination.booked', 18)
    def test_financially_booked2(self):
        self.assertEqual(self.ppc.financially_booked, 10)

    @mock.patch('trs.core.ProjectPersonCombination.budget', 10)
    @mock.patch('trs.core.ProjectPersonCombination.booked', 18)
    def test_left_to_book1(self):
        self.assertEqual(self.ppc.left_to_book, 0)

    @mock.patch('trs.core.ProjectPersonCombination.budget', 10)
    @mock.patch('trs.core.ProjectPersonCombination.booked', 8)
    def test_left_to_book2(self):
        self.assertEqual(self.ppc.left_to_book, 2)

    @mock.patch('trs.core.ProjectPersonCombination.financially_booked', 10)
    @mock.patch('trs.core.ProjectPersonCombination.hourly_tariff', 20)
    def test_turnover(self):
        self.assertEqual(self.ppc.turnover, 200)

    @mock.patch('trs.core.ProjectPersonCombination.left_to_book', 10)
    @mock.patch('trs.core.ProjectPersonCombination.hourly_tariff', 20)
    def test_left_to_turn_over(self):
        self.assertEqual(self.ppc.left_to_turn_over, 200)

    def test_hourly_tariff1(self):
        self.assertEqual(self.ppc.hourly_tariff, 0)

    def test_hourly_tariff2(self):
        factories.WorkAssignmentFactory.create(
            assigned_to=self.person,
            assigned_on=self.project,
            hourly_tariff=80)
        factories.WorkAssignmentFactory.create(
            assigned_to=self.person,
            assigned_on=self.project,
            hourly_tariff=20)
        self.assertEqual(self.ppc.hourly_tariff, 100)

    def test_is_project_leader1(self):
        self.assertEqual(self.ppc.is_project_leader, False)

    def test_is_project_leader2(self):
        self.project.project_leader = self.person
        self.assertEqual(self.ppc.is_project_leader, True)

    def test_is_project_manager1(self):
        self.assertEqual(self.ppc.is_project_manager, False)

    def test_is_project_manager2(self):
        self.project.project_manager = self.person
        self.assertEqual(self.ppc.is_project_manager, True)
