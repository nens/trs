import datetime

from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
import mock

from trs import views
from trs.management.commands.update_weeks import ensure_year_weeks_are_present
from trs.tests import factories


REINOUTS_BIRTHDATE = datetime.date(year=1972, month=12, day=25)


class BaseMixinTestCase(TestCase):
    def setUp(self):
        self.view = views.BaseMixin()
        self.view.request = RequestFactory().get("/")

    def test_today(self):
        self.assertTrue(self.view.today)

    def test_active_projects_is_iterable(self):
        # if no one is logged in, we should be iterable, too.
        self.view.request = RequestFactory().get("/")
        self.view.request.user = AnonymousUser()
        self.assertEqual(self.view.active_projects, [])

    def test_active_person(self):
        # if no one is logged in, we should be iterable, too.
        user = factories.UserFactory.create()  # This creates a person, too
        self.view.request.user = user
        self.assertEqual(self.view.active_person, user.person)

    def test_active_projects(self):
        ensure_year_weeks_are_present()
        user = factories.UserFactory.create()  # This creates a person, too
        person = user.person
        project1 = factories.ProjectFactory.create(code="p1")
        project2 = factories.ProjectFactory.create(code="p2")
        factories.WorkAssignmentFactory(assigned_to=person, assigned_on=project1)
        factories.WorkAssignmentFactory(assigned_to=person, assigned_on=project2)
        self.view.request.user = person.user
        self.assertEqual(list(self.view.active_projects), [project2, project1])


class PersonsViewTestCase(TestCase):
    def setUp(self):
        self.person1 = factories.PersonFactory.create()
        self.person2 = factories.PersonFactory.create()

    def test_smoke(self):
        ensure_year_weeks_are_present()
        request = RequestFactory().get("/")
        view = views.PersonsView(request=request)
        self.assertEqual(view.lines[1]["person"], self.person2)


class PersonViewTestCase(TestCase):
    def setUp(self):
        self.person = factories.PersonFactory.create()

    def test_smoke(self):
        view = views.PersonView(kwargs={"pk": self.person.pk})
        self.assertEqual(view.person, self.person)


class ProjectsViewTestCase(TestCase):
    def setUp(self):
        self.project1 = factories.ProjectFactory.create()
        self.project2 = factories.ProjectFactory.create()

    def test_smoke(self):
        user = factories.UserFactory.create()
        request = RequestFactory().get("/")
        request.user = user
        view = views.ProjectsView(request=request)
        self.assertEqual(view.lines[1]["project"], self.project1)


class ProjectViewTestCase(TestCase):
    def setUp(self):
        self.project = factories.ProjectFactory.create()

    def test_smoke(self):
        view = views.ProjectView(kwargs={"pk": self.project.pk})
        self.assertEqual(view.project, self.project)


class BookingViewTestCase(TestCase):
    def test_active_year_week_explicit(self):
        year = 1972
        week = 51
        year_week = factories.YearWeekFactory.create(year=year, week=week)
        view = views.BookingView(kwargs={"year": year, "week": week})
        self.assertEqual(view.active_year_week, year_week)

    def test_active_year_week_implicit(self):
        year_week = factories.YearWeekFactory.create(
            year=1972, week=51, first_day=REINOUTS_BIRTHDATE
        )

        def _mock_date():
            return year_week

        with mock.patch("trs.views.this_year_week", _mock_date):
            view = views.BookingView(kwargs={})
            self.assertEqual(view.active_year_week, year_week)

    def test_active_first_day(self):
        factories.YearWeekFactory.create(
            year=1972, week=51, first_day=REINOUTS_BIRTHDATE
        )
        view = views.BookingView(kwargs={"year": 1972, "week": 51})
        self.assertEqual(view.active_first_day, REINOUTS_BIRTHDATE)

    def test_year_weeks_to_display(self):
        factories.YearWeekFactory.create()  # week 1
        year_week2 = factories.YearWeekFactory.create()
        year_week3 = factories.YearWeekFactory.create()
        year_week4 = factories.YearWeekFactory.create()
        year_week5 = factories.YearWeekFactory.create()
        factories.YearWeekFactory.create()  # week 6
        current_year_week = year_week4
        # So we want 2 and 3 before, 4 itself and 5 as the next one.
        view = views.BookingView(
            kwargs={"year": current_year_week.year, "week": current_year_week.week}
        )
        self.assertEqual(
            list(view.year_weeks_to_display),
            [year_week2, year_week3, year_week4, year_week5],
        )


class RatingsOveriewTestCase(TestCase):
    def setUp(self):
        self.project1 = factories.ProjectFactory.create()
        self.project2 = factories.ProjectFactory.create()
        self.project3 = factories.ProjectFactory.create()
        self.project4 = factories.ProjectFactory.create()
        # One with both, one with one rating each, one without any.
        self.project1.rating_projectteam = 8
        self.project2.rating_projectteam = 7
        self.project2.rating_customer = 3
        self.project3.rating_customer = 5
        self.project1.save()
        self.project2.save()
        self.project3.save()

        request = RequestFactory().get("/")
        self.view = views.RatingsOverview(request=request)

    def test_projects(self):
        self.assertEquals(len(self.view.projects), 3)

    def test_average1(self):
        self.assertEquals(self.view.average_rating_projectteam, 7.5)

    def test_average2(self):
        self.assertEquals(self.view.average_rating_customer, 4)


class FinancialOverviewTestCase(TestCase):
    def setUp(self):
        factories.GroupFactory.create()
        factories.GroupFactory.create()

    def test_smoke(self):
        ensure_year_weeks_are_present()
        request = RequestFactory().get("/")
        view = views.FinancialOverview(request=request)
        self.assertEquals(len(list(view.download_links())), 4)


class FinancialCsvViewTestCase(TestCase):
    def setUp(self):
        self.group = factories.GroupFactory.create()

    def test_smoke(self):
        ensure_year_weeks_are_present()
        request = RequestFactory().get("/")
        view = views.FinancialCsvView(request=request, kwargs={})
        self.assertTrue(list(view.csv_lines))

    def test_smoke_with_group(self):
        ensure_year_weeks_are_present()
        request = RequestFactory().get("/")
        view = views.FinancialCsvView(request=request, kwargs={"pk": self.group.id})
        self.assertTrue(list(view.csv_lines))


class SearchViewTestCase(TestCase):
    def setUp(self):
        self.project1 = factories.ProjectFactory.create(code="Bring wood")
        self.project2 = factories.ProjectFactory.create(code="Bring oil",
                                                        description="for the pyre")
        self.person1 = factories.PersonFactory.create(name="Faramir")

    def test_without_query(self):
        request = RequestFactory().get("/")
        view = views.SearchView(request=request, kwargs={})
        self.assertFalse(view.projects())
        self.assertFalse(view.persons())
        self.assertFalse(view.show_nothing_found_warning())

    def test_query_project(self):
        request = RequestFactory().get("/", data={"q": "wood"})
        view = views.SearchView(request=request)
        self.assertEquals(len(view.projects()), 1)
        self.assertFalse(view.persons())
        self.assertFalse(view.show_nothing_found_warning())

    def test_query_project_multiple(self):
        request = RequestFactory().get("/", data={"q": "bring"})
        view = views.SearchView(request=request)
        self.assertEquals(len(view.projects()), 2)
        self.assertFalse(view.persons())
        self.assertFalse(view.show_nothing_found_warning())

    def test_query_person(self):
        request = RequestFactory().get("/", data={"q": "faramir"})
        view = views.SearchView(request=request)
        self.assertFalse(view.projects())
        self.assertEquals(len(view.persons()), 1)
        self.assertFalse(view.show_nothing_found_warning())

    def test_query_nothing_found(self):
        request = RequestFactory().get("/", data={"q": "hobbit"})
        view = views.SearchView(request=request)
        self.assertFalse(view.projects())
        self.assertFalse(view.persons())
        self.assertTrue(view.show_nothing_found_warning())
