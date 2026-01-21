import calendar
import datetime
import logging
import statistics
import time
import urllib.parse
from collections import OrderedDict, defaultdict
from copy import deepcopy
from decimal import Decimal

import xlsxwriter
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from trs import core
from trs.forms import ProjectTeamForm, SearchForm
from trs.models import (
    MPC,
    Booking,
    BudgetItem,
    Group,
    Invoice,
    Payable,
    Person,
    PersonChange,
    Project,
    ThirdPartyEstimate,
    WbsoProject,
    WorkAssignment,
    YearWeek,
    this_year_week,
)
from trs.templatetags.trs_formatting import hours as format_as_hours

logger = logging.getLogger(__name__)

BIG_PROJECT_SIZE: int = 200  # hours
MAX_BAR_HEIGHT: int = 50  # px
BAR_WIDTH: int = 75  # px
BACK_TEMPLATE: str = '<div><small><a href="{url}">&larr; {text}</a></small></div>'
MONTHS: list[str] = [
    "Januari",
    "Februari",
    "Maart",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Augustus",
    "September",
    "Oktober",
    "November",
    "December",
]
TOTAL_COMPANY: str = "Totaal"
NO_FILTER = "---"


class LoginAndPermissionsRequiredMixin:
    """See http://stackoverflow.com/a/10304880/27401"""

    def has_form_permissions(self) -> bool:
        """Especially for forms, return whether we have the necessary perms.

        Overwrite this in subclasses.
        """
        return True

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.has_form_permissions():
            raise PermissionDenied
        return super().dispatch(*args, **kwargs)


def try_and_find_matching_person(user):
    full_name = user.first_name + " " + user.last_name
    full_name = full_name.lower()
    full_name = full_name.replace(",", " ")
    full_name = full_name.replace("-", " ")
    parts = full_name.split(" ")
    names = Person.objects.all().values_list("name", flat=True)
    for part in parts:
        names = [name for name in names if part in name.lower()]
    if len(names) > 1:
        logger.warn(
            "Tried matching %s, but found more than one match: %s", full_name, names
        )
        return
    if len(names) == 1:
        return Person.objects.get(name=names[0])


def home(request):
    return redirect("trs.booking")


class BaseMixin:
    template_name: str = "trs/base.html"
    title: str = "TRS tijdregistratiesysteem"
    filters_and_choices = []
    normally_visible_filters = None
    results_for_selection_pager = None

    @cached_property
    def current_get_params(self):
        params = {}
        for filter in self.prepared_filters:
            if filter["active"]:
                params[filter["param"]] = filter["active_value"]

        return urllib.parse.urlencode(params)

    @cached_property
    def prepared_filters(self):
        filters = deepcopy(self.filters_and_choices)

        # Figure out which params are at non-default values
        non_default_params = {}
        for filter in filters:
            param = filter["param"]
            from_get = self.request.GET.get(param, None)
            if from_get is None:
                continue
            if from_get == filter["default"]:
                continue
            allowed_values = [choice["value"] for choice in filter["choices"]]
            if from_get not in allowed_values:
                continue
            non_default_params[param] = from_get

        # Calculate query string for choices and determine active choices.
        # Also add queries for the database.
        for filter in filters:
            param = filter["param"]
            get_params = deepcopy(non_default_params)
            filter["active"] = param in get_params
            if self.normally_visible_filters is None:
                filter["hidden"] = False
            else:
                filter["hidden"] = not (
                    param in self.normally_visible_filters or filter["active"]
                )

            active_value = get_params.get(param, filter["default"])
            filter["active_value"] = active_value

            if param in get_params:
                # Do not include our own previous value
                get_params.pop(param)

            filter["url"] = urllib.parse.urlencode(get_params)
            for choice in filter["choices"]:
                get_params[param] = choice["value"]
                choice["query_string"] = urllib.parse.urlencode(get_params)
                choice["active"] = choice["value"] == active_value
                if choice["active"]:
                    filter["q"] = choice["q"]

        return filters

    @cached_property
    def for_selection_pager(self):
        if not self.results_for_selection_pager:
            return
        return [
            {
                "name": str(result),
                "url": result.get_absolute_url() + "?from_selection_pager",
            }
            for result in self.results_for_selection_pager
        ]

    @cached_property
    def filters(self):
        # BBB version of prepared_filters()
        return {
            filter["param"]: filter["active_value"] for filter in self.prepared_filters
        }

    @cached_property
    def today(self):
        return datetime.date.today()

    @cached_property
    def year(self):
        # Customization based on year happens a lot.
        return int(self.request.GET.get("year", this_year_week().year))

    @cached_property
    def is_custom_year(self):
        return self.year != this_year_week().year

    # Note on security-related items: see ``security.rst`` for a quick
    # intro. It might not be 100% accurate, but it is close.

    @cached_property
    def active_person(self):
        if self.request.user.is_anonymous:
            logger.debug("Anonymous user")
            return
        persons = Person.objects.filter(user=self.request.user)
        if not persons:
            logger.warn(
                "Person matching request's user %s not found.", self.request.user
            )
            # Try to couple based on username. One-time action. This means you
            # can prepare persons beforehand and have them automatically
            # coupled the moment they sign in. A real automatic LDAP coupling
            # would have been better, but python-ldap doesn't work with python
            # 3 yet.
            person = try_and_find_matching_person(self.request.user)
            if person:
                logger.info(
                    "Found not-yet-coupled person %s for user %s.",
                    person,
                    self.request.user,
                )
                person.user = self.request.user
                person.cache_indicator += -1  # Don't trigger a re-calc
                person.save()
                return person
        if persons:
            person = persons[0]
            return person

    @cached_property
    def active_projects(self):
        if not self.active_person:
            return []
        return list(self.active_person.filtered_assigned_projects())

    @cached_property
    def sidebar_person(self):
        return self.active_person

    @cached_property
    def sidebar_person_year_info(self):
        if not self.sidebar_person:
            return
        return core.get_pyc(person=self.sidebar_person, year=self.year)

    @cached_property
    def sidebar_person_previous_year_reminder(self):
        if not self.sidebar_person:
            return
        if self.is_custom_year:
            return
        if self.today.month != 1:
            return

        previous_year = self.year - 1
        to_book = core.get_pyc(person=self.sidebar_person, year=previous_year).to_book
        if to_book["friendly"] == 0:
            # The to_book mechanism filters it out.
            return
        to_book["link"] = (
            reverse("trs.booking.overview", kwargs={"pk": self.sidebar_person.id})
            + f"?year={previous_year}"
        )
        return to_book

    @cached_property
    def selected_tab(self):
        recognized = ["booking", "projects", "persons", "overviews"]
        for path_element in recognized:
            path_start = f"/{path_element}/"
            if self.request.path.startswith(path_start):
                return path_element

    @cached_property
    def admin_override_active(self):
        # Allow an admin to see everything for debug purposes.
        if self.request.user.is_superuser:
            if "admin_override_active" not in self.request.session:
                self.request.session["admin_override_active"] = False
            if "all" in self.request.GET:
                self.request.session["admin_override_active"] = True
            if "notall" in self.request.GET:
                self.request.session["admin_override_active"] = False
            if self.request.session["admin_override_active"]:
                return True

    @cached_property
    def can_edit_and_see_everything(self):
        if self.admin_override_active:
            return True
        if self.active_person.is_office_management:
            return True

    @cached_property
    def can_see_everything(self):
        if self.can_edit_and_see_everything:
            return True
        if self.active_person.is_management:
            return True

    @cached_property
    def is_project_management(self):
        """If viewing a project, return whether we're manager/leader/boss."""
        if not hasattr(self, "project"):
            return False
        if self.can_edit_and_see_everything:
            return True
        if self.active_person in [
            self.project.project_manager,
            self.project.project_leader,
        ]:
            return True

    @cached_property
    def sentry_javascript_dsn(self):
        return getattr(settings, "SENTRY_JAVASCRIPT_DSN", None)

    @cached_property
    def group_choices(self):
        return list(Group.objects.all().values_list("pk", "name"))

    @cached_property
    def mpc_choices(self):
        return list(MPC.objects.all().values_list("pk", "name"))


class BaseView(LoginAndPermissionsRequiredMixin, TemplateView, BaseMixin):
    pass


class PersonsView(BaseView):
    title = "Medewerkers"
    normally_visible_filters = ["status", "group", "year"]

    @cached_property
    def results_for_selection_pager(self):
        return self.persons

    @cached_property
    def available_years(self):
        years_booked_in = list(
            Booking.objects.filter()
            .values("year_week__year")
            .distinct()
            .values_list("year_week__year", flat=True)
        )
        current_year = this_year_week().year
        if current_year not in years_booked_in:
            # Corner case if no one has booked yet in this year :-)
            years_booked_in.append(current_year)
        return years_booked_in

    @cached_property
    def filters_and_choices(self):
        result = [
            {
                "title": "Status",
                "param": "status",
                "default": "active",
                "choices": [
                    {
                        "value": "active",
                        "title": "huidige medewerkers",
                        "q": Q(archived=False),
                    },
                    {
                        "value": "archived",
                        "title": "gearchiveerde medewerkers",
                        "q": Q(archived=True),
                    },
                    {"value": "all", "title": "geen filter", "q": Q()},
                ],
            },
            {
                "title": "Groep",
                "param": "group",
                "default": "all",
                "choices": [{"value": "all", "title": NO_FILTER, "q": Q()}]
                + [
                    {
                        "value": str(group.id),
                        "title": group.name,
                        "q": Q(group=group.id),
                    }
                    for group in Group.objects.all()
                ]
                + [{"value": "geen", "title": "Zonder groep", "q": Q(group=None)}],
            },
            {
                "title": "Jaar",
                "param": "year",
                "default": str(this_year_week().year),
                "choices": [
                    {"value": str(year), "title": year, "q": Q()}
                    for year in reversed(self.available_years)
                ],
            },
        ]
        return result

    @property
    def template_name(self):
        if self.can_view_elaborate_version:
            return "trs/persons.html"
        return "trs/persons-simple.html"

    @cached_property
    def can_view_elaborate_version(self):
        if self.can_see_everything:
            return True

    @cached_property
    def persons(self):
        q_objects = [filter["q"] for filter in self.prepared_filters]
        return Person.objects.filter(*q_objects)

    @cached_property
    def selected_year(self):
        return self.filters.get("year")

    @cached_property
    def lines(self):
        return [
            {"person": person, "pyc": core.get_pyc(person, year=self.selected_year)}
            for person in self.persons
        ]

    @cached_property
    def total_turnover(self):
        return sum([line["pyc"].turnover for line in self.lines])

    @cached_property
    def total_left_to_book(self):
        return sum([line["pyc"].left_to_book_external for line in self.lines])

    @cached_property
    def total_left_to_turn_over(self):
        return sum([line["pyc"].left_to_turn_over for line in self.lines])


class PersonView(BaseView):
    template_name = "trs/person.html"

    filters_and_choices = [
        {
            "title": "Filter",
            "param": "filter",
            "default": "active",
            "choices": [
                {
                    "value": "active",
                    "title": "huidige projecten",
                    "q": Q(archived=False),
                },
                {
                    "value": "all",
                    "title": "alle projecten (inclusief archief)",
                    "q": Q(),
                },
            ],
        }
    ]

    @cached_property
    def person(self):
        return Person.objects.get(pk=self.kwargs["pk"])

    @cached_property
    def title(self):
        return self.person.name

    @cached_property
    def sidebar_person(self):
        if self.can_see_everything:
            return self.person
        if self.person == self.active_person:
            return self.person

    @cached_property
    def can_see_internal_projects(self):
        if self.can_see_everything:
            return True
        if self.active_person == self.person:
            return True

    @cached_property
    def can_edit_person(self):
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def can_edit_person_changes(self):
        if self.person.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def can_see_financials(self):
        if self.can_see_everything:
            return True
        if self.active_person == self.person:
            return True

    @cached_property
    def pyc(self):
        return core.get_pyc(self.person)

    @cached_property
    def all_projects(self):
        q_objects = [filter["q"] for filter in self.prepared_filters]
        return self.person.assigned_projects().filter(*q_objects)

    @cached_property
    def projects(self):
        if self.can_see_internal_projects:
            return self.all_projects
        return [project for project in self.all_projects if not project.internal]

    @cached_property
    def lines(self):
        """Return project info per line"""
        # TODO: somewhat similar to BookingView.
        result = []
        # Budget query.
        relevant_work_assignments = WorkAssignment.objects.filter(
            assigned_to=self.person, assigned_on__in=self.projects
        ).values("assigned_on", "hours", "hourly_tariff")
        budgets = {
            item["assigned_on"]: (item["hours"]) for item in relevant_work_assignments
        }
        hourly_tariffs = {
            item["assigned_on"]: (item["hourly_tariff"])
            for item in relevant_work_assignments
        }
        # Hours worked query.
        booked_per_project = (
            Booking.objects.filter(booked_by=self.person, booked_on__in=self.projects)
            .values("booked_on")
            .annotate(models.Sum("hours"))
        )
        booked_this_year_per_project = (
            Booking.objects.filter(
                booked_by=self.person,
                booked_on__in=self.projects,
                year_week__year=this_year_week().year,
            )
            .values("booked_on")
            .annotate(models.Sum("hours"))
        )
        booked = {
            item["booked_on"]: (item["hours__sum"] or 0) for item in booked_per_project
        }
        booked_this_year = {
            item["booked_on"]: (item["hours__sum"] or 0)
            for item in booked_this_year_per_project
        }

        for project in self.projects:
            line = {"project": project}
            line["budget"] = budgets.get(project.id, 0)
            line["booked"] = booked.get(project.id, 0)
            line["booked_this_year"] = booked_this_year.get(project.id, 0)
            line["booked_previous_years"] = line["booked"] - line["booked_this_year"]
            line["is_overbooked"] = line["booked"] > line["budget"]
            line["left_to_book"] = max(0, line["budget"] - line["booked"])
            line["is_project_leader"] = project.project_leader_id == self.person.id
            line["is_project_manager"] = project.project_manager_id == self.person.id
            line["hourly_tariff"] = hourly_tariffs.get(project.id, 0)
            line["turnover"] = (
                min(line["budget"], line["booked"]) * line["hourly_tariff"]
            )
            result.append(line)
        return result

    @cached_property
    def extra_roles(self):
        num_project_leader_roles = sum(
            [
                project.project_leader_id == self.person.id
                for project in self.all_projects
            ]
        )
        num_project_manager_roles = sum(
            [
                project.project_manager_id == self.person.id
                for project in self.all_projects
            ]
        )
        roles = []
        if num_project_leader_roles:
            roles.append(f"{num_project_leader_roles} keer projectleider")
        if num_project_manager_roles:
            roles.append(f"{num_project_manager_roles} keer projectmanager")
        if self.person.is_management:
            roles.append("in management")
        if self.person.is_office_management:
            roles.append("in office management")
        if not roles:
            return "Geen"
        return ", ".join(roles)


class PersonKPIView(PersonView):
    template_name = "trs/kpi.html"

    def has_form_permissions(self):
        if self.can_see_everything:
            return True
        if self.active_person == self.person:
            return True
        return False

    @cached_property
    def lines(self):
        pyc = core.get_pyc(person=self.sidebar_person, year=self.year)
        project_ids = pyc.per_project.keys()
        result = []
        for project in Project.objects.filter(id__in=project_ids):
            line = {}
            line.update(pyc.per_project[project.id])
            line["project"] = project
            result.append(line)
        return result

    @cached_property
    def available_years(self):
        years_person_booked_in = list(
            Booking.objects.filter(booked_by=self.sidebar_person)
            .values("year_week__year")
            .distinct()
            .values_list("year_week__year", flat=True)
        )
        current_year = this_year_week().year
        if current_year not in years_person_booked_in:
            # Corner case if you haven't booked yet in this year :-)
            years_person_booked_in.append(current_year)
        return years_person_booked_in


class BookingOverview(PersonView):
    template_name = "trs/booking_overview.html"

    def has_form_permissions(self):
        if self.can_see_everything:
            return True
        if self.active_person == self.person:
            return True
        return False

    @cached_property
    def year(self):
        return int(self.request.GET.get("year", this_year_week().year))

    @cached_property
    def available_years(self):
        years_i_booked_in = list(
            Booking.objects.filter(booked_by=self.person)
            .values("year_week__year")
            .distinct()
            .values_list("year_week__year", flat=True)
        )
        current_year = this_year_week().year
        if current_year not in years_i_booked_in:
            # Corner case if you haven't booked yet in this year :-)
            years_i_booked_in.append(current_year)
        return years_i_booked_in

    @cached_property
    def lines(self):
        booked_this_year_per_week = (
            Booking.objects.filter(booked_by=self.person, year_week__year=self.year)
            .values("year_week__week")
            .annotate(models.Sum("hours"))
        )
        booked_per_week = {
            item["year_week__week"]: (item["hours__sum"] or 0)
            for item in booked_this_year_per_week
        }
        start_hours_amount = (
            self.person.person_changes.filter(year_week__year__lt=self.year).aggregate(
                models.Sum("hours_per_week")
            )["hours_per_week__sum"]
            or 0
        )
        changes_this_year = (
            self.person.person_changes.filter(year_week__year=self.year)
            .values("year_week__week")
            .annotate(models.Sum("hours_per_week"))
        )
        changes_per_week = {
            change["year_week__week"]: (change["hours_per_week__sum"])
            for change in changes_this_year
        }
        result = []
        to_book = start_hours_amount
        for year_week in YearWeek.objects.filter(year=self.year):
            to_book += changes_per_week.get(year_week.week, 0)
            to_book_this_week = to_book - year_week.num_days_missing * 8
            # num_days_missing is only relevant for the first and last week of
            # a year.
            booked = booked_per_week.get(year_week.week, 0)
            klass = ""
            hint = ""
            if booked < to_book_this_week:
                klass = "danger"
                hint = f"Te boeken: {(to_book_this_week)}"
            if (
                year_week.year == this_year_week().year
                and year_week.week >= this_year_week().week
            ):
                # Don't complain about this or future weeks.
                klass = ""
            result.append(
                {"year_week": year_week, "booked": booked, "klass": klass, "hint": hint}
            )
        return result


class FreeOverview(PersonView):
    template_name = "trs/free_overview.html"

    def has_form_permissions(self):
        if self.can_see_everything:
            return True
        if self.active_person == self.person:
            return True
        return False

    @cached_property
    def year(self):
        return int(self.request.GET.get("year", this_year_week().year))

    @cached_property
    def available_years(self):
        years_i_booked_in = list(
            Booking.objects.filter(booked_by=self.person)
            .values("year_week__year")
            .distinct()
            .values_list("year_week__year", flat=True)
        )
        current_year = this_year_week().year
        if current_year not in years_i_booked_in:
            # Corner case if you haven't booked yet in this year :-)
            years_i_booked_in.append(current_year)
        return years_i_booked_in

    @cached_property
    def free_project_ids(self):
        return sorted(
            self.person.assigned_projects()
            .filter(
                Q(description__icontains="verlof") | Q(description__icontains="feest")
            )
            .values_list("id", flat=True)
        )

    @cached_property
    def free_projects(self):
        my_bookings = self.person.bookings.filter(year_week__year=self.year)
        return Project.objects.filter(
            bookings__in=my_bookings, id__in=self.free_project_ids
        ).distinct()

    @cached_property
    def lines(self):
        booked_this_year_per_week_per_project = Booking.objects.filter(
            booked_by=self.person,
            year_week__year=self.year,
            booked_on__in=self.free_projects,
        ).values("year_week__week", "booked_on", "hours")
        weeks = {}
        empty_week = {}
        for project in self.free_projects:
            empty_week[project.id] = 0
        for year_week in YearWeek.objects.filter(year=self.year):
            weeks[year_week.week] = deepcopy(empty_week)
        for booking in booked_this_year_per_week_per_project:
            weeks[booking["year_week__week"]][booking["booked_on"]] = booking["hours"]
        result = []
        for year_week in YearWeek.objects.filter(year=self.year):
            hours = [
                weeks[year_week.week][project.id] for project in self.free_projects
            ]
            line = {"year_week": year_week, "hours": hours}
            result.append(line)
        return result


class ProjectsView(BaseView):
    @cached_property
    def results_for_selection_pager(self):
        if not self.projects.has_next():
            # List is too long, no use grabbing the full list just for pagination now
            # that we have "infinite scrolling" with htmx.
            return self.projects

    @cached_property
    def filters_and_choices(self):
        result = [
            {
                "title": "Status",
                "param": "status",
                "default": "active",
                "choices": [
                    {
                        "value": "active",
                        "title": "huidige projecten",
                        "q": Q(archived=False),
                    },
                    {
                        "value": "archived",
                        "title": "gearchiveerde projecten",
                        "q": Q(archived=True),
                    },
                    {"value": "all", "title": NO_FILTER, "q": Q()},
                ],
            },
            {
                "title": "Subsidie",
                "param": "is_subsidized",
                "default": "all",
                "choices": [
                    {"value": "all", "title": NO_FILTER, "q": Q()},
                    {
                        "value": "false",
                        "title": "geen subsidie",
                        "q": Q(is_subsidized=False),
                    },
                    {
                        "value": "true",
                        "title": "subsidieprojecten",
                        "q": Q(is_subsidized=True),
                    },
                ],
            },
            {
                "title": "Groep",
                "param": "group",
                "default": "all",
                "choices": [{"value": "all", "title": NO_FILTER, "q": Q()}]
                + [
                    {
                        "value": str(group.id),
                        "title": group.name,
                        "q": Q(group=group.id),
                    }
                    for group in Group.objects.all()
                ]
                + [{"value": "geen", "title": "Zonder groep", "q": Q(group=None)}],
            },
            {
                "title": "MPC",
                "param": "mpc",
                "default": "all",
                "choices": [{"value": "all", "title": NO_FILTER, "q": Q()}]
                + [
                    {
                        "value": str(mpc.id),
                        "title": mpc.name,
                        "q": Q(mpc=mpc.id),
                    }
                    for mpc in MPC.objects.all()
                ]
                + [{"value": "geen", "title": "Zonder MPC", "q": Q(mpc=None)}],
            },
            {
                "title": "Projectleider",
                "param": "project_leader",
                "default": "all",
                "choices": [{"value": "all", "title": NO_FILTER, "q": Q()}]
                + [
                    {
                        "value": str(person.id),
                        "title": person.name,
                        "q": Q(project_leader=person.id),
                    }
                    for person in self.project_leaders
                ]
                + [
                    {"value": "geen", "title": "zonder PL", "q": Q(project_leader=None)}
                ],
            },
            {
                "title": "Projectmanager",
                "param": "project_manager",
                "default": "all",
                "choices": [{"value": "all", "title": NO_FILTER, "q": Q()}]
                + [
                    {
                        "value": str(person.id),
                        "title": person.name,
                        "q": Q(project_manager=person.id),
                    }
                    for person in self.project_managers
                ]
                + [
                    {
                        "value": "geen",
                        "title": "zonder PM",
                        "q": Q(project_manager=None),
                    }
                ],
            },
            {
                "title": "Al gestart",
                "param": "started",
                "default": "all",
                "choices": [
                    {"value": "all", "title": NO_FILTER, "q": Q()},
                    {
                        "value": "true",
                        "title": "ja",
                        "q": Q(start__lte=this_year_week()),
                    },
                    {
                        "value": "false",
                        "title": "nee",
                        "q": Q(start__gt=this_year_week()),
                    },
                ],
            },
            {
                "title": "Al geeindigd",
                "param": "ended",
                "default": "all",
                "choices": [
                    {"value": "all", "title": NO_FILTER, "q": Q()},
                    {"value": "true", "title": "ja", "q": Q(end__lt=this_year_week())},
                    {
                        "value": "false",
                        "title": "nee",
                        "q": Q(end__gte=this_year_week()),
                    },
                ],
            },
            {
                "title": "Rapportcijfers",
                "param": "ratings",
                "default": "all",
                "choices": [
                    {"value": "all", "title": NO_FILTER, "q": Q()},
                    {
                        "value": "both",
                        "title": "allebei ingevuld",
                        "q": (Q(rating_projectteam__gte=1) & Q(rating_customer__gte=1)),
                    },
                    {
                        "value": "todo",
                        "title": "nog niet compleet",
                        "q": (Q(rating_projectteam=None) | Q(rating_customer=None)),
                    },
                ],
            },
        ]
        return result

    @cached_property
    def normally_visible_filters(self):
        result = ["status", "group", "mpc", "project_leader", "project_manager"]
        if self.can_see_everything:
            result += [
                "is_subsidized",
                "started",
                "ended",
                "ratings",
            ]
        return result

    title = "Projecten"

    @cached_property
    def project_leaders(self):
        return Person.objects.filter(projects_i_lead__archived=False).distinct()

    @cached_property
    def project_managers(self):
        return Person.objects.filter(projects_i_manage__archived=False).distinct()

    @property
    def template_name(self):
        if self.can_view_elaborate_version:
            return "trs/projects.html"
        return "trs/projects-simple.html"

    @cached_property
    def can_add_project(self):
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def can_view_elaborate_version(self):
        if self.can_see_everything:
            return True
        if self.filters["project_leader"]:
            if self.filters["project_leader"] == self.active_person.id:
                return True
        if self.filters["project_manager"]:
            if self.filters["project_manager"] == self.active_person.id:
                return True

    @cached_property
    def projects(self):
        q_objects = [filter["q"] for filter in self.prepared_filters]
        result = Project.objects.filter(*q_objects)
        if not self.can_view_elaborate_version:
            result = result.filter(hidden=False)

        # Pagination, mostly for the looooooong archive projects list.
        page = self.request.GET.get("page")
        paginator = Paginator(result, 150)
        try:
            result = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            result = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of
            # results.
            result = paginator.page(paginator.num_pages)

        return result

    @cached_property
    def lines(self):
        # Used for the elaborate view (projects.html)
        result = []
        invoices_per_project = (
            Invoice.objects.filter(project__in=self.projects)
            .values("project")
            .annotate(models.Sum("amount_exclusive"))
            .order_by()
        )
        # ^^^ .order_by() is needed to prevent a weird grouping issue. See
        # https://docs.djangoproject.com/en/1.6/topics/db/aggregation/
        # #interaction-with-default-ordering-or-order-by
        invoice_amounts = {
            item["project"]: item["amount_exclusive__sum"]
            for item in invoices_per_project
        }

        for project in self.projects:
            line = {}
            line["project"] = project
            if project.overbooked_percentage() > 50:
                klass = "danger"
            elif project.overbooked_percentage():
                klass = "warning"
            else:
                klass = "default"
            line["klass"] = klass
            invoice_amount = invoice_amounts.get(project.id, 0)
            turnover = project.turnover()
            costs = project.costs()
            income = project.income()
            reservation = project.reservation
            if project.contract_amount:
                invoice_amount_percentage = round(
                    invoice_amount / project.contract_amount * 100
                )
            else:  # Division by zero.
                invoice_amount_percentage = None
            if turnover + costs + reservation - income:
                invoice_versus_turnover_percentage = round(
                    invoice_amount / (turnover + costs + reservation - income) * 100
                )
            else:
                invoice_versus_turnover_percentage = None
            line["contract_amount"] = project.contract_amount
            line["invoice_amount"] = invoice_amount
            line["turnover"] = turnover
            line["reservation"] = project.reservation
            line["other_costs"] = costs - income
            line["well_booked"] = project.well_booked()
            line["overbooked"] = project.overbooked()
            line["left_to_book"] = project.left_to_book()
            line["person_loss"] = project.person_loss()
            line["person_costs_incl_reservation"] = (
                project.person_costs_incl_reservation()
            )
            line["left_to_turn_over"] = project.left_to_turn_over()

            line["invoice_amount_percentage"] = invoice_amount_percentage
            line["invoice_versus_turnover_percentage"] = (
                invoice_versus_turnover_percentage
            )
            result.append(line)
        return result

    @cached_property
    def totals(self):
        return {
            key: sum([line[key] for line in self.lines]) or 0
            for key in [
                "turnover",
                "person_costs_incl_reservation",
                "reservation",
                "other_costs",
            ]
        }

    @cached_property
    def total_invoice_amount_percentage(self):
        result = {}
        result["contract_amount"] = sum(
            [line["contract_amount"] for line in self.lines]
        )
        result["invoice_amount"] = sum([line["invoice_amount"] for line in self.lines])
        if result["contract_amount"]:
            percentage = round(
                result["invoice_amount"] / result["contract_amount"] * 100
            )
        else:  # Division by zero.
            percentage = None
        result["percentage"] = percentage
        return result


class ProjectsLossView(ProjectsView):
    @property
    def template_name(self):
        if self.can_view_elaborate_version:
            return "trs/projects_loss.html"
        return "trs/projects-simple.html"

    @cached_property
    def totals(self):
        return {
            key: sum([line[key] for line in self.lines]) or 0
            for key in [
                "well_booked",
                "overbooked",
                "left_to_book",
                "turnover",
                "person_loss",
                "left_to_turn_over",
                "reservation",
            ]
        }


class ProjectView(BaseView):
    template_name = "trs/project.html"

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["pk"])

    @cached_property
    def title(self):
        return f"Project {self.project.code}: {self.project.description}"

    @cached_property
    def can_view_team(self):
        if not self.project.hidden:
            # Normally everyone can see it.
            return True
        if self.is_project_management:
            return True
        if self.can_see_everything:
            return True

    @cached_property
    def can_edit_project(self):
        # True for admin even when the project is archived: you must be able
        # to un-set the archive bit. To compensate for this, the title of the
        # edit page has a big fat "you're editing an archived project!"
        # warning.
        if self.can_edit_and_see_everything:
            return True
        if self.project.archived:
            return False
        if self.is_project_management:
            return True

    @cached_property
    def can_edit_financials(self):
        if self.project.archived:
            return False
        if self.is_project_management:
            return True

    @cached_property
    def can_edit_project_financials(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def can_see_financials(self):
        if self.can_see_everything:
            return True
        if self.is_project_management:
            return True
        if self.active_person in self.project.assigned_persons():
            return True

    @cached_property
    def can_see_project_financials(self):
        if self.can_see_everything:
            return True
        if self.is_project_management:
            return True
        if self.active_person in self.project.assigned_persons():
            # Since 2 feb 2015.
            if not self.project.hidden:
                return True

    @cached_property
    def show_bid_and_confirmation_dates(self):
        """Should we show the bid_send_date and confirmation_date?

        These are new fields and we won't show them for older projects
        as that just clutters up the interface. So... for pre-2015
        projects *with* a contract amount we'll hide them if they're
        not filled in.

        For internal projects, we'll also ignore them.
        """
        if self.project.internal:
            return False
        if self.project.bid_send_date or self.project.confirmation_date:
            return True
        if self.project.start.year < 2015 and self.project.contract_amount:
            # Old project with already a contract amount set. Keep it that way.
            return False
        if self.project.archived:
            # Don't bother about archived old projects.
            return False
        return True

    @cached_property
    def lines(self):
        result = []
        # Budget query.
        relevant_work_assignments = WorkAssignment.objects.filter(
            assigned_to__in=self.persons, assigned_on=self.project
        ).values("assigned_to", "hours", "hourly_tariff")
        budgets = {
            item["assigned_to"]: (item["hours"]) for item in relevant_work_assignments
        }
        hourly_tariffs = {
            item["assigned_to"]: (item["hourly_tariff"])
            for item in relevant_work_assignments
        }
        # Hours worked query.
        booked_per_person = (
            Booking.objects.filter(booked_by__in=self.persons, booked_on=self.project)
            .values("booked_by")
            .annotate(models.Sum("hours"))
        )
        booked = {
            item["booked_by"]: (item["hours__sum"] or 0) for item in booked_per_person
        }

        for person in self.persons:
            line = {"person": person}
            line["budget"] = budgets.get(person.id, 0)
            line["booked"] = booked.get(person.id, 0)
            line["is_overbooked"] = line["booked"] > line["budget"]
            line["left_to_book"] = max(0, line["budget"] - line["booked"])
            line["is_project_leader"] = self.project.project_leader_id == person.id
            line["is_project_manager"] = self.project.project_manager_id == person.id
            line["hourly_tariff"] = hourly_tariffs.get(person.id, 0)
            tariff = line["hourly_tariff"]
            line["turnover"] = min(line["budget"], line["booked"]) * tariff
            line["loss"] = max(0, (line["booked"] - line["budget"])) * tariff
            line["left_to_turn_over"] = line["left_to_book"] * tariff
            line["planned_turnover"] = line["budget"] * tariff
            line["desired_hourly_tariff"] = min(
                person.standard_hourly_tariff(year_week=self.project.start),
                person.standard_hourly_tariff(),
            )
            result.append(line)
        return result

    @cached_property
    def persons(self):
        return self.project.assigned_persons()

    @cached_property
    def total_turnover(self):
        return sum([line["turnover"] for line in self.lines])

    @cached_property
    def total_loss(self):
        return sum([line["loss"] for line in self.lines])

    @cached_property
    def total_turnover_left(self):
        return sum([line["left_to_turn_over"] for line in self.lines])

    @cached_property
    def total_costs(self):
        return (
            self.project.costs()
            + self.project.person_costs_incl_reservation()
            + self.project.third_party_costs()
        )

    @cached_property
    def total_income(self):
        return self.project.contract_amount + self.project.income()

    @cached_property
    def amount_left(self):
        return self.subtotal - self.total_turnover - self.total_turnover_left

    @cached_property
    def total_invoice_exclusive(self):
        return sum(
            [invoice.amount_exclusive for invoice in self.project.invoices.all()]
        )

    @cached_property
    def total_invoice_inclusive(self):
        return sum(
            [invoice.amount_inclusive for invoice in self.project.invoices.all()]
        )

    @cached_property
    def total_third_party_invoices(self):
        return sum([payable.amount for payable in self.project.payables.all()])


class LoginView(FormView, BaseMixin):
    # Reachable as /locallogin/
    template_name = "trs/login.html"
    form_class = AuthenticationForm

    @cached_property
    def success_url(self):
        return reverse("trs.booking")

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super().form_valid(form)


def logout_view(request):
    logout(request)
    return redirect("trs.home")


class BookingView(LoginAndPermissionsRequiredMixin, FormView, BaseMixin):
    template_name = "trs/booking.html"

    def has_form_permissions(self):
        # Warning: this is used as "permission to view the page", not directly
        # permission to edit someone else's bookings.
        if self.can_see_everything:
            return True
        return self.active_person == self.person

    def has_edit_permissions(self):
        # Warning: this is the permission to actually edit your own or someone
        # else's bookings.
        if self.can_edit_and_see_everything:
            return True
        return self.active_person == self.person

    @cached_property
    def editing_for_someone_else(self):
        if not self.has_edit_permissions():
            # Not editing.
            return False
        if self.active_person == self.person:
            # Editing for myself.
            return False
        else:
            # Yes, editing for someone else!
            # Used to print dire warnings.
            return True

    @cached_property
    def person(self):
        person_id = self.kwargs.get("pk")
        if person_id is None:
            return self.active_person
        return Person.objects.get(pk=person_id)

    @cached_property
    def title(self):
        if self.active_person != self.person:
            return f"Boekingen van {self.person}"
        return "Uren boeken"

    @cached_property
    def sidebar_person(self):
        if self.can_see_everything:
            return self.person
        if self.person == self.active_person:
            return self.person

    @cached_property
    def active_year_week(self):
        year = self.kwargs.get("year")
        week = self.kwargs.get("week")
        if year is not None:  # (Week is also not None, then)
            return YearWeek.objects.get(year=year, week=week)
        # Default: this week's first day.
        return this_year_week()

    @cached_property
    def active_first_day(self):
        return self.active_year_week.first_day

    @cached_property
    def year_weeks_to_display(self):
        """Return the active YearWeek, the two previous ones and the next."""
        end = self.active_first_day + datetime.timedelta(days=7)
        start = self.active_first_day - datetime.timedelta(days=2 * 7)
        result = list(
            YearWeek.objects.filter(first_day__lte=end).filter(first_day__gte=start)
        )
        if len(result) > 4:
            # Splitted week at start/end of year problem. We get 5 weeks...
            # Trim off the first or last one depending on whether we're in the
            # first weeks or not.
            if result[2].week < 10:
                result = result[-4:]
            else:
                result = result[:4]
        return result

    @cached_property
    def relevant_projects(self):
        first_week = self.year_weeks_to_display[0]
        latest_week = self.year_weeks_to_display[-1]
        return Project.objects.filter(
            work_assignments__assigned_to=self.person,
            end__gte=first_week,
            start__lte=latest_week,
        ).distinct()

    @cached_property
    def highlight_column(self):
        """Return column number (1-based) of the current week's column."""
        try:
            column_index = self.year_weeks_to_display.index(this_year_week())
        except ValueError:
            return 0
        return column_index + 1

    def get_form_class(self):
        """Return dynamically generated form class."""
        fields = OrderedDict()
        if self.has_edit_permissions:
            # If not, we cannot edit anything, just view.
            for index, project in enumerate(self.relevant_projects):
                field_type = forms.IntegerField(
                    min_value=0,
                    max_value=100,
                    widget=forms.TextInput(
                        attrs={"size": 2, "type": "number", "tabindex": index + 1}
                    ),
                )
                fields[project.code] = field_type
        return type("GeneratedBookingForm", (forms.Form,), fields)

    @cached_property
    def initial(self):
        """Return initial form values."""
        result = {}
        bookings = Booking.objects.filter(
            year_week=self.active_year_week,
            booked_by=self.person,
            booked_on__in=self.relevant_projects,
        ).values("booked_on__code", "hours")
        # TODO: this is per week, it should be per day.
        result = {item["booked_on__code"]: (item["hours"]) for item in bookings}
        return {
            project.code: result.get(project.code, 0)
            for project in self.relevant_projects
        }

    def form_valid(self, form):
        # Note: filtering on inactive (start/end date) projects and on booking
        # year is done in the visual part of the view. It isn't enforced here
        # yet. To do once we start using this as an API.
        start_time = time.time()
        total_difference = 0
        absolute_difference = 0
        for project_code, new_hours in form.cleaned_data.items():
            old_hours = self.initial[project_code]
            difference = new_hours - old_hours
            total_difference += difference
            absolute_difference += abs(difference)
            if difference:
                project = [
                    project
                    for project in self.relevant_projects
                    if project.code == project_code
                ][0]
                booking, _ = Booking.objects.get_or_create(
                    booked_by=self.person,
                    booked_on=project,
                    year_week=self.active_year_week,
                )
                booking.hours = new_hours
                booking.save()

        if absolute_difference:
            if total_difference < 0:
                indicator = total_difference
            elif total_difference > 0:
                indicator = f"+{total_difference}"
            else:  # 0
                indicator = "alleen verschoven"
            if self.editing_for_someone_else:
                messages.warning(
                    self.request, f"Uren van iemand anders aangepast ({indicator})."
                )
            else:
                messages.success(self.request, f"Uren aangepast ({indicator}).")
        else:
            messages.info(self.request, "Niets aan de uren gewijzigd.")
        elapsed = time.time() - start_time
        logger.debug("Handled booking in %s secs", elapsed)
        return super().form_valid(form)

    @cached_property
    def tabindex_submit_button(self):
        return len(self.relevant_projects) + 1

    @cached_property
    def success_url(self):
        return reverse(
            "trs.booking",
            kwargs={
                "pk": self.person.id,
                "year": self.active_year_week.year,
                "week": self.active_year_week.week,
            },
        )

    @cached_property
    def lines(self):
        """Return project plus a set of four hours."""
        result = []
        form = self.get_form(self.get_form_class())
        fields = list(form)  # A form's __iter__ returns 'bound fields'.
        # Prepare booking info as one query.
        booking_table = Booking.objects.filter(
            year_week__in=self.year_weeks_to_display, booked_by=self.person
        ).values("booked_on", "year_week", "hours")
        # ^^^ TODO sum
        bookings = {
            (item["booked_on"], item["year_week"]): item["hours"]
            for item in booking_table
        }
        # Idem for budget
        relevant_work_assignments = WorkAssignment.objects.filter(
            assigned_to=self.person, assigned_on__in=self.relevant_projects
        ).values("assigned_on", "hours")
        budgets = {
            item["assigned_on"]: (item["hours"]) for item in relevant_work_assignments
        }
        # Item for hours worked.
        booked_per_project = (
            Booking.objects.filter(
                booked_by=self.person, booked_on__in=self.relevant_projects
            )
            .values("booked_on")
            .annotate(models.Sum("hours"))
        )
        booked_total = {
            item["booked_on"]: (item["hours__sum"] or 0) for item in booked_per_project
        }

        for project_index, project in enumerate(self.relevant_projects):
            line = {"project": project}
            for index, year_week in enumerate(self.year_weeks_to_display):
                booked = bookings.get((project.id, year_week.id), 0)
                key = f"hours{index}"
                line[key] = booked

            if fields:
                line["field"] = fields[project_index]
                if (
                    project.archived
                    or project.start > self.active_year_week
                    or project.end < self.active_year_week
                    # or self.active_year_week.year < this_year
                ):
                    # Filtering if we're allowed to book or not.
                    line["field"].field.widget.attrs["hidden"] = True
                    line["show_uneditable_value"] = True
            else:
                # No fields: we're only allowed to view the data, not edit it.
                line["field"] = ""
                line["show_uneditable_value"] = True

            line["budget"] = budgets.get(project.id, 0)
            line["booked_total"] = booked_total.get(project.id, 0)
            line["is_overbooked"] = line["booked_total"] > line["budget"]
            line["left_to_book"] = max(0, line["budget"] - line["booked_total"])
            result.append(line)
        return result

    def totals(self):
        return [
            sum([line[f"hours{index}"] for line in self.lines]) for index in range(4)
        ]


class ProjectEditView(LoginAndPermissionsRequiredMixin, UpdateView, BaseMixin):
    template_name = "trs/edit.html"
    model = Project

    @property
    def fields(self):
        if self.can_edit_and_see_everything:
            return [
                "code",
                "description",
                "group",
                "mpc",
                "internal",
                "hidden",
                "hourless",
                "archived",  # Note: archived only on edit view :-)
                "is_subsidized",
                "principal",
                "bid_send_date",
                "confirmation_date",
                "contract_amount",
                "start",
                "end",
                "project_leader",
                "project_manager",
                # Note: the next one is shown only on the edit view!
                "remark",
                "financial_remark",
                "rating_projectteam",
                "rating_projectteam_reason",
                "rating_customer",
                "rating_customer_reason",
                "end",
            ]
        result = [
            "remark",
            "financial_remark",
            "start",
            "end",
            "rating_projectteam",
            "rating_projectteam_reason",
            "rating_customer",
            "rating_customer_reason",
        ]
        return result

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["pk"])

    @cached_property
    def title(self):
        text = "Project aanpassen"
        if self.project.archived:
            text = "OPGEPAST: JE BEWERKT EEN GEARCHIVEERD PROJECT!"
        return text

    def has_form_permissions(self):
        # Editable for admins even when archived as you must be able to un-set
        # the 'archive' bit. If archived, the title warns you in no uncertain
        # way.
        if self.can_edit_and_see_everything:
            return True
        if self.project.archived:
            return False
        if self.is_project_management:
            return True

    def form_valid(self, form):
        messages.success(self.request, "Project aangepast")
        return super().form_valid(form)


class ProjectCreateView(LoginAndPermissionsRequiredMixin, CreateView, BaseMixin):
    template_name = "trs/create-project.html"
    model = Project
    title = "Nieuw project"
    fields = [
        "code",
        "description",
        "group",
        "mpc",
        "internal",
        "hidden",
        "hourless",
        "is_subsidized",
        "principal",
        "bid_send_date",
        "confirmation_date",
        "contract_amount",
        "start",
        "end",
        "project_leader",
        "project_manager",
        "remark",
        "financial_remark",
    ]

    def has_form_permissions(self):
        if self.can_edit_and_see_everything:
            return True

    def form_valid(self, form):
        messages.success(self.request, "Project aangemaakt")
        return super().form_valid(form)

    def latest_projects(self):
        # Note: they're reverse sorted, so we want the first :-)
        external = Project.objects.filter(internal=False, archived=False)[:3]
        internal = Project.objects.filter(internal=True, archived=False)[:3]
        return list(external) + list(internal)


class InvoiceCreateView(LoginAndPermissionsRequiredMixin, CreateView, BaseMixin):
    template_name = "trs/edit.html"
    model = Invoice
    title = "Nieuwe factuur"
    fields = ["date", "number", "description", "amount_exclusive", "vat", "payed"]

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["project_pk"])

    @cached_property
    def success_url(self):
        return reverse("trs.project", kwargs={"pk": self.project.pk})

    def form_valid(self, form):
        form.instance.project = self.project
        messages.success(self.request, "Factuur toegevoegd")
        return super().form_valid(form)


class InvoiceEditView(LoginAndPermissionsRequiredMixin, UpdateView, BaseMixin):
    template_name = "trs/edit-invoice.html"
    model = Invoice
    fields = ["date", "number", "description", "amount_exclusive", "vat", "payed"]

    @property
    def title(self):
        return f"Aanpassen factuur voor {self.project.code}"

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["project_pk"])

    @cached_property
    def invoice(self):
        return Invoice.objects.get(pk=self.kwargs["pk"])

    def edit_action(self):
        if "from_invoice_overview" in self.request.GET:
            return ".?from_invoice_overview"
        if "from_selection_pager" in self.request.GET:
            return ".?from_selection_pager"

    @cached_property
    def success_url(self):
        if "from_invoice_overview" in self.request.GET:
            params = f"?year={self.invoice.date.year}#{self.invoice.id}"
            return reverse("trs.overviews.invoices") + params
        if "from_selection_pager" in self.request.GET:
            return ".?from_selection_pager"
        return reverse("trs.project", kwargs={"pk": self.project.pk})

    def form_valid(self, form):
        messages.success(self.request, "Factuur aangepast")
        return super().form_valid(form)


class PayableCreateView(LoginAndPermissionsRequiredMixin, CreateView, BaseMixin):
    template_name = "trs/edit.html"
    model = Payable
    title = "Nieuwe kosten derden"
    fields = ["date", "number", "description", "amount", "payed"]

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["project_pk"])

    @cached_property
    def success_url(self):
        return reverse("trs.project", kwargs={"pk": self.project.pk})

    def form_valid(self, form):
        form.instance.project = self.project
        messages.success(self.request, "Kosten derden toegevoegd")
        return super().form_valid(form)


class PayableEditView(LoginAndPermissionsRequiredMixin, UpdateView, BaseMixin):
    template_name = "trs/edit.html"
    # ^^^ Note: thise might need to become like edit-invoice.html, with its
    # extra project info.
    model = Payable
    fields = ["date", "number", "description", "amount", "payed"]

    @property
    def title(self):
        return f"Aanpassen kosten derden voor {self.project.code}"

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["project_pk"])

    @cached_property
    def payable(self):
        return Payable.objects.get(pk=self.kwargs["pk"])

    def edit_action(self):
        if "from_payable_overview" in self.request.GET:
            return ".?from_payable_overview"
        if "from_selection_pager" in self.request.GET:
            return ".?from_selection_pager"

    @cached_property
    def success_url(self):
        if "from_payable_overview" in self.request.GET:
            params = f"?year={self.payable.date.year}#{self.payable.id}"
            return reverse("trs.overviews.payables") + params
        if "from_selection_pager" in self.request.GET:
            return ".?from_selection_pager"
        return reverse("trs.project", kwargs={"pk": self.project.pk})

    def form_valid(self, form):
        messages.success(self.request, "Kosten derden aangepast")
        return super().form_valid(form)


class PersonEditView(LoginAndPermissionsRequiredMixin, UpdateView, BaseMixin):
    template_name = "trs/edit.html"
    model = Person
    fields = ["name", "user", "group", "is_management", "archived"]

    @cached_property
    def person(self):
        return Person.objects.get(pk=self.kwargs["pk"])

    @cached_property
    def title(self):
        text = "Medewerker aanpassen"
        if self.person.archived:
            text = "OPGEPAST: JE BEWERKT EEN GEARCHIVEERDE MEDEWERKER!"
        return text

    def has_form_permissions(self):
        # Archived persons are editable: we must be able to un-set the archive
        # bit. The title warns us, though.
        if self.can_edit_and_see_everything:
            return True

    def form_valid(self, form):
        messages.success(self.request, "Medewerker aangepast")
        return super().form_valid(form)


class TeamUpdateView(LoginAndPermissionsRequiredMixin, FormView, BaseMixin):
    """View for auto-adding internal members (if needed)."""

    template_name = "trs/team-update.html"

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["pk"])

    @cached_property
    def title(self):
        return f"Projectteam updaten voor {self.project.code}"

    form_class = forms.Form  # Yes, an empty form.

    @cached_property
    def missing_internal_persons(self):
        if self.project.internal:
            already_assigned = self.project.assigned_persons()
            active_persons = Person.objects.filter(archived=False)
            missing = [
                person for person in active_persons if person not in already_assigned
            ]
            return missing
        return []

    def form_valid(self, form):
        num_added = 0
        for person in self.missing_internal_persons:
            WorkAssignment.objects.get_or_create(
                assigned_on=self.project, assigned_to=person
            )
            num_added += 1
        messages.success(self.request, f"{num_added} teamleden toegevoegd")
        return super().form_valid(form)

    @cached_property
    def success_url(self):
        return reverse("trs.project.budget", kwargs={"pk": self.project.pk})

    @cached_property
    def back_url(self):
        url = self.project.get_absolute_url()
        text = "Terug naar het project"
        return mark_safe(BACK_TEMPLATE.format(url=url, text=text))


class SearchView(BaseView):
    template_name = "trs/search.html"
    form_class = SearchForm

    @cached_property
    def search_text(self):
        q = self.request.GET.get("q", None)
        if not q:
            return
        form = SearchForm({"q": q})
        if form.is_valid():
            return form.cleaned_data["q"]

    def projects(self):
        if not self.search_text:
            return
        return Project.objects.filter(
            Q(code__icontains=self.search_text)
            | Q(description__icontains=self.search_text)
        )

    def persons(self):
        if not self.search_text:
            return
        return Person.objects.filter(
            Q(name__icontains=self.search_text)
            | Q(description__icontains=self.search_text)
            | Q(user__username__icontains=self.search_text)
        )

    def show_nothing_found_warning(self):
        """Return if we found nothing, but only when we actually searched.

        Used for UI feedback.
        """
        if not self.search_text:
            # We didn't search yet, so no need to show a warning.
            return False
        if self.projects() or self.persons():
            # Results! So no warning
            return False
        # We searched, but didn't get any results.
        return True


class DeleteView(LoginAndPermissionsRequiredMixin, FormView, BaseMixin):
    template_name = "trs/delete.html"

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["pk"])

    form_class = forms.Form  # Yes, an empty form.

    @cached_property
    def back_url(self):
        url = self.project.get_absolute_url()
        text = "Terug naar het project"
        return mark_safe(BACK_TEMPLATE.format(url=url, text=text))


class InvoiceDeleteView(DeleteView):
    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def invoice(self):
        return Invoice.objects.get(pk=self.kwargs["invoice_pk"])

    @cached_property
    def title(self):
        return f"Verwijder factuur {self.invoice.number} uit {self.project.code}"

    def form_valid(self, form):
        self.invoice.delete()
        self.project.save()  # Increment cache key.
        messages.success(
            self.request,
            f"{self.invoice.number} verwijderd uit {self.project.code}",
        )
        return super().form_valid(form)

    @cached_property
    def success_url(self):
        return reverse("trs.project", kwargs={"pk": self.project.pk})


class PayableDeleteView(DeleteView):
    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def payable(self):
        return Payable.objects.get(pk=self.kwargs["payable_pk"])

    @cached_property
    def title(self):
        return f"Verwijder kosten derden {self.payable.number} uit {self.project.code}"

    def form_valid(self, form):
        self.payable.delete()
        self.project.save()  # Increment cache key.
        messages.success(
            self.request,
            f"{self.payable.number} verwijderd uit {self.project.code}",
        )
        return super().form_valid(form)

    @cached_property
    def success_url(self):
        return reverse("trs.project", kwargs={"pk": self.project.pk})


class ProjectBudgetEditView(BaseView):
    template_name = "trs/project-budget-edit.html"

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.is_project_management:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["pk"])

    @cached_property
    def title(self):
        return f"Projectbegroting van {self.project.code} bewerken"

    @cached_property
    def can_edit_hours(self):
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True

    @cached_property
    def can_add_team_member(self):
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True

    @property
    def can_delete_team_member(self):
        # Note: team members can in any case only be deleted if they haven't
        # yet booked any hours on the project.
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True

    @cached_property
    def back_url(self):
        url = self.project.get_absolute_url()
        text = "Terug naar het project"
        return mark_safe(BACK_TEMPLATE.format(url=url, text=text))

    @cached_property
    def success_url(self):
        return reverse("trs.project.budget", kwargs={"pk": self.project.pk})

    def estimate_formset_factory(self):
        return forms.inlineformset_factory(
            Project, ThirdPartyEstimate, fields=["description", "amount"], extra=3
        )

    def budget_item_formset_factory(self):
        return forms.inlineformset_factory(
            Project,
            BudgetItem,
            fk_name="project",
            fields=["description", "amount", "to_project"],
            extra=3,
        )

    def work_assignment_formset_factory(self):
        return forms.inlineformset_factory(
            Project,
            WorkAssignment,
            fields=["assigned_to", "hours", "hourly_tariff"],
            extra=4,
        )

    def get(self, *args, **kwargs):
        self.project_form = ProjectTeamForm(instance=self.project)
        ThirdPartyEstimateFormSet = self.estimate_formset_factory()
        self.estimate_formset = ThirdPartyEstimateFormSet(instance=self.project)
        BudgetItemFormSet = self.budget_item_formset_factory()
        self.budget_item_formset = BudgetItemFormSet(instance=self.project)
        WorkAssignmentFormset = self.work_assignment_formset_factory()
        self.work_assignment_formset = WorkAssignmentFormset(instance=self.project)
        self.adjust_work_assignment_formset()
        # fields['amount'].widget.attrs['disabled'] = 'disabled'
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.project_form = ProjectTeamForm(
            data=self.request.POST, instance=self.project
        )
        ThirdPartyEstimateFormSet = self.estimate_formset_factory()
        self.estimate_formset = ThirdPartyEstimateFormSet(
            data=self.request.POST, instance=self.project
        )
        BudgetItemFormSet = self.budget_item_formset_factory()
        self.budget_item_formset = BudgetItemFormSet(
            data=self.request.POST, instance=self.project
        )
        WorkAssignmentFormset = self.work_assignment_formset_factory()
        self.work_assignment_formset = WorkAssignmentFormset(
            data=self.request.POST, instance=self.project
        )
        self.adjust_work_assignment_formset()

        if (
            self.project_form.is_valid()
            and self.estimate_formset.is_valid()
            and self.budget_item_formset.is_valid()
            and self.work_assignment_formset.is_valid()
        ):
            logger.debug("All forms are valid")
            self.project_form.save()
            self.estimate_formset.save()
            self.budget_item_formset.save()
            self.work_assignment_formset.save()

            if self.project.code.endswith(".0"):
                # .0 = offertetraject, dus nultarief.
                for work_assignment, _ in self.work_assignment_formset.changed_objects:
                    if work_assignment.hourly_tariff != 0:
                        work_assignment.hourly_tariff = 0
                        work_assignment.save()
                        msg = f".0 project: uurtarief {work_assignment.assigned_to} op 0 gezet"
                        messages.info(self.request, msg)
            else:
                # Geen standaard nultarief, dus geef nieuwe projectleden het
                # standaardtarief (tenzij het al op een andere waarde gezet is).
                for work_assignment in self.work_assignment_formset.new_objects:
                    if work_assignment.hourly_tariff == 0:
                        work_assignment.hourly_tariff = (
                            work_assignment.assigned_to.standard_hourly_tariff()
                        )
                        work_assignment.save()
                        msg = f"Uurtarief {work_assignment.assigned_to} aangepast naar standaardtarief"
                        messages.info(self.request, msg)

            self.project.refresh_from_db()
            if self.project.left_to_dish_out() < -1:
                msg = f"Je boekt {round(self.project.left_to_dish_out())} in het rood"
                messages.error(self.request, msg)

            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(self.request, "Corrigeer de fouten hieronder")
            context = self.get_context_data(**kwargs)
            context["project_form"] = self.project_form
            context["estimate_formset"] = self.estimate_formset
            context["budget_item_formset"] = self.budget_item_formset
            context["work_assignment_formset"] = self.work_assignment_formset
            return self.render_to_response(context)

    def add_team_member(self, id):
        person = Person.objects.get(id=id)
        msg = f"{person.name} is aan het team toegevoegd"
        WorkAssignment.objects.get_or_create(
            assigned_on=self.project, assigned_to=person
        )
        logger.info(msg)
        messages.success(self.request, msg)

    @cached_property
    def can_edit_hourly_tariff(self):
        if self.is_project_management:
            return True

    @cached_property
    def budgets_and_tariffs(self):
        budget_per_person = WorkAssignment.objects.filter(
            assigned_on=self.project
        ).values("assigned_to", "hours", "hourly_tariff")
        budgets = {item["assigned_to"]: (item["hours"]) for item in budget_per_person}
        hourly_tariffs = {
            item["assigned_to"]: (item["hourly_tariff"]) for item in budget_per_person
        }
        return budgets, hourly_tariffs

    def adjust_work_assignment_formset(self):
        """Mark fields as disabled and add some extra info."""
        budgets, hourly_tariffs = self.budgets_and_tariffs
        booked_per_person = (
            Booking.objects.filter(booked_on=self.project)
            .values("booked_by")
            .annotate(models.Sum("hours"))
        )
        booked = {
            item["booked_by"]: (item["hours__sum"] or 0) for item in booked_per_person
        }

        for form in self.work_assignment_formset:
            if form.initial:
                # Existing work assignment. We don't want the person to be swapped, so
                # we disable the person dropdown, for instance.
                form.fields["assigned_to"].disabled = True
                person = Person.objects.get(id=form.initial["assigned_to"])
                if person.archived or (not self.can_edit_hours):
                    form.fields["hours"].disabled = True
                if person.archived or (not self.can_edit_hourly_tariff):
                    form.fields["hourly_tariff"].disabled = True
                if booked.get(person.id) or not self.can_delete_team_member:
                    form.fields["DELETE"].disabled = True

                # Add a few attributes to help the template that renders it.
                form.person = person
                form.booked = format_as_hours(booked.get(person.id, 0))
                form.costs = hourly_tariffs.get(person.id, 0) * budgets.get(
                    person.id, 0
                )
                form.is_project_manager = self.project.project_manager_id == person.id
                form.is_project_leader = self.project.project_leader_id == person.id

                # Don't delete the PM/PL.
                if form.is_project_leader or form.is_project_manager:
                    form.fields["DELETE"].disabled = True


class PersonChangeView(LoginAndPermissionsRequiredMixin, CreateView, BaseMixin):
    template_name = "trs/person-change.html"
    model = PersonChange
    fields = [
        "hours_per_week",
        "target",
        "standard_hourly_tariff",
    ]

    def has_form_permissions(self):
        if self.person.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def person(self):
        return Person.objects.get(pk=self.kwargs["pk"])

    @cached_property
    def title(self):
        return (
            f"Wijzig gegevens voor {self.person.name} (stand {self.chosen_year_week})"
        )

    @cached_property
    def success_url(self):
        return self.person.get_absolute_url()

    @cached_property
    def edit_action(self):
        return f".?year_week={self.chosen_year_week.as_param()}"

    @cached_property
    def chosen_year_week(self):
        if "year_week" not in self.request.GET:
            # Return the current week, unless we're at the start of the year.
            if this_year_week().week < 5:
                return YearWeek.objects.filter(year=this_year_week().year).first()
            else:
                return this_year_week()
        year, week = self.request.GET["year_week"].split("-")
        return YearWeek.objects.get(year=int(year), week=int(week))

    def year_week_suggestions(self):
        current_year = this_year_week().year
        next_year = current_year + 1
        return [
            # (yyyy-ww, title)
            (
                YearWeek.objects.filter(year=current_year).first().as_param(),
                f"Begin {current_year} (begin dit jaar)",
            ),
            (this_year_week().as_param(), "Nu"),
            (
                YearWeek.objects.filter(year=next_year).first().as_param(),
                f"Begin {next_year} (begin volgend jaar)",
            ),
        ]

    def all_year_weeks(self):
        # Well, all... 2013 is our TRS start year.
        return YearWeek.objects.filter(year__gte=2013)

    @cached_property
    def previous_changes(self):
        changes = list(
            PersonChange.objects.filter(person=self.person)
            .values("year_week")
            .annotate(
                models.Sum("hours_per_week"),
                models.Sum("target"),
                models.Sum("standard_hourly_tariff"),
            )
        )
        relevant_weeks = YearWeek.objects.filter(
            id__in=[change["year_week"] for change in changes]
        )
        for index, change in enumerate(changes):
            change["year_week_str"] = relevant_weeks[index].as_param()
        return changes

    @cached_property
    def initial(self):
        """Return initial form values.

        Turn the decimals into integers already."""
        return {
            "hours_per_week": int(
                self.person.hours_per_week(year_week=self.chosen_year_week)
            ),
            "standard_hourly_tariff": int(
                self.person.standard_hourly_tariff(year_week=self.chosen_year_week)
            ),
            "target": int(self.person.target(year_week=self.chosen_year_week)),
        }

    def form_valid(self, form):
        form.instance.person = self.person
        # We let the form machinery set the values, but they need to be
        # re-calculated for the initial values: they're used as culumative
        # values.
        hours_per_week = form.instance.hours_per_week or 0  # Adjust for None
        standard_hourly_tariff = form.instance.standard_hourly_tariff or 0
        target = form.instance.target or 0  # Adjust for None
        form.instance.hours_per_week = hours_per_week - self.initial["hours_per_week"]
        form.instance.standard_hourly_tariff = (
            standard_hourly_tariff - self.initial["standard_hourly_tariff"]
        )
        form.instance.target = target - self.initial["target"]
        form.instance.year_week = self.chosen_year_week

        adjusted = []
        if form.instance.hours_per_week:
            adjusted.append("werkweek")
        if form.instance.standard_hourly_tariff:
            adjusted.append("standaard uurtarief")
        if form.instance.target:
            adjusted.append("target")
        if adjusted:
            msg = " en ".join(adjusted)
            msg = f"{msg.capitalize()} aangepast"
            msg += f" (ingaande {self.chosen_year_week.formatted_first_day})"
            messages.success(self.request, msg)
        else:
            messages.info(self.request, "Niets aan te passen")
        return super().form_valid(form)


class OverviewsView(BaseView):
    template_name = "trs/overviews.html"

    @cached_property
    def previous_year(self):
        return this_year_week().year - 1


class InvoicesView(BaseView):
    template_name = "trs/invoices.html"
    normally_visible_filters = ["status", "year"]

    @cached_property
    def results_for_selection_pager(self):
        return self.invoices

    @cached_property
    def filters_and_choices(self):
        result = [
            {
                "title": "Status",
                "param": "status",
                "default": "all",
                "choices": [
                    {"value": "all", "title": "alles", "q": Q()},
                    {"value": "false", "title": "nog niet betaald", "q": Q(payed=None)},
                ],
            },
            {
                "title": "Jaar",
                "param": "year",
                "default": str(this_year_week().year),
                "choices": [
                    {"value": str(year), "title": year, "q": Q(date__year=year)}
                    for year in reversed(self.available_years)
                ]
                + [{"value": "all", "title": "alle jaren", "q": Q()}],
            },
            {
                "title": "Maand",
                "param": "month",
                "default": "all",
                "choices": [
                    {"value": "all", "title": "alles", "q": Q()},
                    {"value": "1", "title": "jan", "q": Q(date__month=1)},
                    {"value": "2", "title": "feb", "q": Q(date__month=2)},
                    {"value": "3", "title": "mrt", "q": Q(date__month=3)},
                    {"value": "4", "title": "apr", "q": Q(date__month=4)},
                    {"value": "5", "title": "mei", "q": Q(date__month=5)},
                    {"value": "6", "title": "jun", "q": Q(date__month=6)},
                    {"value": "7", "title": "jul", "q": Q(date__month=7)},
                    {"value": "8", "title": "aug", "q": Q(date__month=8)},
                    {"value": "9", "title": "sep", "q": Q(date__month=9)},
                    {"value": "10", "title": "okt", "q": Q(date__month=10)},
                    {"value": "11", "title": "nov", "q": Q(date__month=11)},
                    {"value": "12", "title": "dec", "q": Q(date__month=12)},
                ],
            },
        ]

        return result

    def has_form_permissions(self):
        return self.can_see_everything

    @cached_property
    def year(self):
        return self.filters["year"]

    @cached_property
    def available_years(self):
        this_year = this_year_week().year
        first_date = Invoice.objects.all().first().date
        first_year = first_date.year
        return list(range(first_year, this_year + 1))

    @cached_property
    def invoices(self):
        q_objects = [filter["q"] for filter in self.prepared_filters]
        result = Invoice.objects.filter(*q_objects)
        return result.select_related("project").order_by("-date", "-number")

    @cached_property
    def total_exclusive(self):
        return sum([invoice.amount_exclusive or 0 for invoice in self.invoices])

    @cached_property
    def total_inclusive(self):
        return sum([invoice.amount_inclusive or 0 for invoice in self.invoices])


class InvoicesPerMonthOverview(BaseView):
    template_name = "trs/invoices-per-month.html"

    def has_form_permissions(self):
        return self.can_see_everything

    @cached_property
    def years(self):
        this_year = this_year_week().year
        return sorted([this_year - i for i in range(5)])

    @cached_property
    def months(self):
        return range(1, 13)

    @cached_property
    def years_and_months(self):
        invoices = Invoice.objects.all().values("date", "amount_exclusive")
        result = {
            year: {month: Decimal(0) for month in self.months} for year in self.years
        }
        for invoice in invoices:
            year = invoice["date"].year
            month = invoice["date"].month
            if year not in self.years:
                continue
            result[year][month] += invoice["amount_exclusive"]
        return result

    @cached_property
    def rows(self):
        result = []
        base_url = reverse("trs.overviews.invoices") + "?year=%s&month=%s"
        for month in self.months:
            row = {"month": month, "amounts": []}
            for year in self.years:
                value = self.years_and_months[year][month]
                url = base_url % (year, month)
                row["amounts"].append({"value": value, "url": url})
            result.append(row)
        return result


class PayablesView(BaseView):
    template_name = "trs/payables.html"
    normally_visible_filters = ["status", "year", "projectstatus", "group", "mpc"]

    @cached_property
    def results_for_selection_pager(self):
        return self.payables

    @cached_property
    def filters_and_choices(self):
        result = [
            {
                "title": "Status",
                "param": "status",
                "default": "false",
                "choices": [
                    {
                        "value": "false",
                        "title": "nog niet uitbetaald",
                        "q": Q(payed=None),
                    },
                    {
                        "value": "true",
                        "title": "uitbetaald",
                        "q": Q(payed__isnull=False),
                    },
                    {"value": "all", "title": "alles", "q": Q()},
                ],
            },
            {
                "title": "Jaar (v/d factuurdatum)",
                "param": "year",
                "default": str(this_year_week().year),
                "choices": [
                    {"value": str(year), "title": year, "q": Q(date__year=year)}
                    for year in reversed(self.available_years)
                ]
                + [{"value": "all", "title": "alle jaren", "q": Q()}],
            },
            {
                "title": "Projectstatus",
                "param": "projectstatus",
                "default": "all",
                "choices": [
                    {"value": "all", "title": "geen filter", "q": Q()},
                    {
                        "value": "active",
                        "title": "actieve projecten",
                        "q": Q(project__archived=False),
                    },
                    {
                        "value": "archived",
                        "title": "gearchiveerde projecten",
                        "q": Q(project__archived=True),
                    },
                ],
            },
            {
                "title": "Groep",
                "param": "group",
                "default": "all",
                "choices": [{"value": "all", "title": NO_FILTER, "q": Q()}]
                + [
                    {
                        "value": str(group.id),
                        "title": group.name,
                        "q": Q(project__group=group.id),
                    }
                    for group in Group.objects.all()
                ]
                + [
                    {
                        "value": "geen",
                        "title": "Zonder groep",
                        "q": Q(project__group=None),
                    }
                ],
            },
            {
                "title": "MPC",
                "param": "mpc",
                "default": "all",
                "choices": [{"value": "all", "title": NO_FILTER, "q": Q()}]
                + [
                    {
                        "value": str(mpc.id),
                        "title": mpc.name,
                        "q": Q(mpc=mpc.id),
                    }
                    for mpc in MPC.objects.all()
                ]
                + [{"value": "geen", "title": "Zonder MPC", "q": Q(mpc=None)}],
            },
        ]

        return result

    def has_form_permissions(self):
        return self.can_see_everything

    @cached_property
    def year(self):
        return self.filters["year"]

    @cached_property
    def available_years(self):
        first_date = Payable.objects.all().first().date
        first_year = first_date.year
        last_date = Payable.objects.all().last().date
        last_year = last_date.year
        if last_year < this_year_week().year:
            last_year = this_year_week().year
        return list(range(first_year, last_year + 1))

    @cached_property
    def payables(self):
        q_objects = [filter["q"] for filter in self.prepared_filters]
        result = Payable.objects.filter(*q_objects)
        return result.select_related("project").order_by("-date", "-number")

    @cached_property
    def total(self):
        return sum([payable.amount or 0 for payable in self.payables])


class ChangesOverview(BaseView):
    template_name = "trs/changes.html"

    @cached_property
    def filters_and_choices(self):
        result = [
            {
                "title": "Periode",
                "param": "num_weeks",
                "default": "1",
                "choices": [
                    {"value": "1", "title": "alleen deze week", "q": Q()},
                    {"value": "2", "title": "ook vorige week", "q": Q()},
                    {"value": "4", "title": "volledige maand", "q": Q()},
                ],
            },
            {
                "title": "Projecten",
                "param": "total",
                "default": "true",
                "choices": [
                    {"value": "true", "title": "alle projecten", "q": Q()},
                    {
                        "value": "false",
                        "title": "alleen de projecten waar je PL/PM voor bent",
                        "q": Q(),
                    },
                ],
            },
        ]
        return result

    @cached_property
    def num_weeks(self):
        """Return number of weeks to use for the summaries."""
        return int(self.filters["num_weeks"])

    @cached_property
    def relevant_year_weeks(self):
        end = self.today
        start = self.today - datetime.timedelta(days=(self.num_weeks + 1) * 7)
        # ^^^ num_weeks + 1 to get a bit of padding halfway the week.
        return YearWeek.objects.filter(first_day__lte=end).filter(first_day__gte=start)

    @cached_property
    def start_week(self):
        return self.relevant_year_weeks[0]

    @cached_property
    def project_budget_changes(self):
        start = self.start_week.first_day
        is_project_leader = models.Q(project__project_leader=self.active_person)
        is_project_manager = models.Q(project__project_manager=self.active_person)
        added_after_start = models.Q(added__gte=start)
        budget_items = BudgetItem.objects.all()
        if not (self.can_see_everything and self.filters["total"]):
            # Normally restrict it to relevant projects for you, but a manager
            # can see everything if desired.
            budget_items = budget_items.filter(is_project_manager | is_project_leader)
        budget_items = budget_items.filter(added_after_start).select_related("project")
        projects = {
            budget_item.project.id: {"project": budget_item.project, "added": []}
            for budget_item in budget_items
        }
        for budget_item in budget_items:
            projects[budget_item.project.id]["added"].append(budget_item)
            # Hm, this can be done simpler, but now it matches the invoice
            # changes...
        return projects.values()

    @cached_property
    def project_invoice_changes(self):
        start = self.start_week.first_day
        is_project_leader = models.Q(project__project_leader=self.active_person)
        is_project_manager = models.Q(project__project_manager=self.active_person)
        added_after_start = models.Q(date__gte=start)
        payed_after_start = models.Q(date__gte=start)

        invoices = Invoice.objects.all()
        if not (self.can_see_everything and self.filters["total"]):
            # Normally restrict it to relevant projects for you, but a manager
            # can see everything if desired.
            invoices = invoices.filter(is_project_manager | is_project_leader)
        invoices = invoices.filter(
            added_after_start | payed_after_start
        ).select_related("project")
        projects = {
            invoice.project.id: {"project": invoice.project, "added": [], "payed": []}
            for invoice in invoices
        }
        for invoice in invoices:
            if invoice.date >= start:
                projects[invoice.project.id]["added"].append(invoice)
            if invoice.payed is not None and invoice.payed >= start:
                projects[invoice.project.id]["payed"].append(invoice)
        return projects.values()

    @cached_property
    def are_there_changes(self):
        return self.project_budget_changes or self.project_invoice_changes


class ProjectLeadersAndManagersView(BaseView):
    template_name = "trs/pl_pm.html"

    @cached_property
    def project_leaders(self):
        return Person.objects.filter(projects_i_lead__archived=False).distinct()

    @cached_property
    def project_managers(self):
        return Person.objects.filter(projects_i_manage__archived=False).distinct()


def _django_model_instance_to_string(worksheet, row, col, instance, format=None):
    # See https://xlsxwriter.readthedocs.io/working_with_data.html#writing-user-types
    return worksheet.write_string(row, col, str(instance), format)


class ExcelResponseMixin:
    prepend_lines = []
    header_line = []
    excel_lines = []

    def title_to_filename(self):
        name = self.title.lower()
        if getattr(self, "small_title", None):
            name = name + " " + self.small_title.lower()
        # Brute force
        name = [
            char for char in name if char in "abcdefghijklmnopqrstuvwxyz-_ 0123456789"
        ]
        name = "".join(name)
        name = name.replace(" ", "_")
        return name

    @property
    def excel_filename(self):
        return self.title_to_filename()

    def render_to_response(self, context, **response_kwargs):
        """Return a excel response instead of a rendered template."""
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # noqa
        )
        filename = self.excel_filename + ".xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        workbook = xlsxwriter.Workbook(response)
        worksheet = workbook.add_worksheet()
        worksheet.add_write_handler(Group, _django_model_instance_to_string)
        worksheet.add_write_handler(MPC, _django_model_instance_to_string)
        worksheet.add_write_handler(Person, _django_model_instance_to_string)
        worksheet.add_write_handler(Project, _django_model_instance_to_string)
        worksheet.add_write_handler(YearWeek, _django_model_instance_to_string)

        row_number = 0
        for line in self.prepend_lines:
            worksheet.write_row(row_number, 0, line)
            row_number += 1  # yeah, right...
        worksheet.write_row(row_number, 0, self.header_line)
        row_number += 1
        for line in self.excel_lines:
            # Note: line should be a list of values.
            worksheet.write_row(row_number, 0, line)
            row_number += 1

        workbook.close()
        return response


class ProjectsExcelView(ExcelResponseMixin, ProjectsView):
    def has_form_permissions(self):
        return self.can_view_elaborate_version

    header_line = [
        "Code",
        "Omschrijving",
        "Opdrachtgever",
        "Groep",
        "MPC",
        "Intern",
        "Gesubsidieerd",
        "Gearchiveerd",
        "Start",
        "Einde",
        "PL",
        "PM",
        "Opdrachtsom",
        "Kosten derden",
        "Netto opdrachtsom",
        "Software ontwikkeling",
        "Afdracht",
        "Opdrachtbevestiging binnen",
        "Cijfer team",
        "Cijfer klant",
        "Gefactureerd",
        "Omzet",
        "Toegekende uren",
        "Geboekte uren",
        "Goed geboekt",
        "Verliesuren",
        "Personele kosten incl reservering",
        "Overige kosten",
        "Gefactureerd t.o.v. opdrachtsom",
        "Gefactureerd t.o.v. omzet + extra kosten",
        "Gemiddelde tarief",
        "Gerealiseerde tarief",
        "",
        "Uren binnen budget",
        "Uren buiten budget",
        "Werkvoorraad",
        "",
        "Omzet",
        "Budgetoverschijding",
        "Nog om te zetten",
        "",
        "Reservering",
        "Nog te verdelen",
        "",
        "Opmerking",
        "Financiele opmerking",
    ]

    @property
    def excel_lines(self):
        for line in self.lines:
            project = line["project"]
            remark = ""
            financial_remark = ""
            if project.remark:
                remark = "   ".join(project.remark.splitlines())
            if project.financial_remark:
                financial_remark = "   ".join(project.financial_remark.splitlines())
            result = [
                project.code,
                project.description.replace(",", " "),
                project.principal,
                project.group,
                project.mpc,
                project.internal,
                project.is_subsidized,
                project.archived,
                project.start.first_day,
                project.end.first_day,
                project.project_leader,
                project.project_manager,
                project.contract_amount,
                project.third_party_costs(),
                project.net_contract_amount(),
                project.software_development,
                project.profit,
                project.confirmation_date,
                project.rating_projectteam,
                project.rating_customer,
                line["invoice_amount"],
                line["turnover"],
                project.hour_budget(),
                project.well_booked() + project.overbooked(),
                project.well_booked(),
                project.overbooked(),
                project.person_costs_incl_reservation(),
                line["other_costs"],
                line["invoice_amount_percentage"],
                line["invoice_versus_turnover_percentage"],
                project.weighted_average_tariff(),
                project.realized_average_tariff(),
                "",
                line["well_booked"],
                line["overbooked"],
                line["left_to_book"],
                "",
                line["turnover"],
                line["person_loss"],
                line["left_to_turn_over"],
                "",
                line["reservation"],
                project.left_to_dish_out(),
                "",
                remark,
                financial_remark,
            ]
            yield (result)


class PersonsExcelView(ExcelResponseMixin, PersonsView):
    def has_form_permissions(self):
        return self.can_view_elaborate_version

    header_line = [
        "Naam",
        "Nog te boeken",
        "Buiten budget geboekt",
        "Binnen budget percentage",
        "Extern geboekt",
        "Intern geboekt",
        "Extern percentage",
        "Intern percentage",
        "Target percentage",
        "Target",
        "Omzet",
        "Werkvoorraad",
        "Werkvoorraad als omzet",
    ]

    @property
    def excel_lines(self):
        for line in self.lines:
            person = line["person"]
            pyc = line["pyc"]
            result = [
                person.name,
                pyc.to_book["hours"],
                pyc.overbooked,
                pyc.well_booked_percentage,
                pyc.booked_external,
                pyc.booked_internal,
                pyc.billable_percentage,
                pyc.unbillable_percentage,
                pyc.target_percentage,
                pyc.target,
                pyc.turnover,
                pyc.left_to_book_external,
                pyc.left_to_turn_over,
            ]
            yield result


class ProjectExcelView(ExcelResponseMixin, ProjectView):
    def has_form_permissions(self):
        return self.can_see_project_financials

    @cached_property
    def weeks(self):
        return YearWeek.objects.filter(
            first_day__gte=self.project.start.first_day,
            first_day__lte=self.project.end.first_day,
        )

    @cached_property
    def bookings_per_week_per_person(self):
        bookings = (
            Booking.objects.filter(booked_on=self.project, year_week__in=self.weeks)
            .values("booked_by", "year_week")
            .annotate(models.Sum("hours"))
        )
        return {
            (booking["booked_by"], booking["year_week"]): (booking["hours__sum"])
            for booking in bookings
        }

    @property
    def prepend_lines(self):
        return [
            ["Code", self.project.code],
            ["Naam", self.project.description],
            ["Opdrachtgever", self.project.principal],
            [],
            [],
        ]

    @property
    def header_line(self):
        result = [
            "Naam",
            "Uren achter met boeken",
            "PM/PL",
            "Toegekende uren",
            "Tarief",
            "Kosten",
            "Inkomsten",
            "Geboekt",
            "Omzet",
            "Verlies",
            "",
        ]
        result += [week.as_param() for week in self.weeks]
        return result

    @property
    def excel_lines(self):
        for line in self.lines:
            person = line["person"]
            pl = (person == self.project.project_leader) and "PL" or ""
            pm = (person == self.project.project_manager) and "PM" or ""
            result = [
                person.name,
                person.to_book()["hours"],
                " ".join([pl, pm]),
                line["budget"],
                line["hourly_tariff"],
                line["planned_turnover"],
                "",
                line["booked"],
                line["turnover"],
                line["loss"],
                "",
            ]
            result += [
                self.bookings_per_week_per_person.get((person.pk, week.pk), 0)
                for week in self.weeks
            ]

            yield result

        yield (["Reservering", "", "", "", "", self.project.reservation])

        yield (
            [
                "Subtotaal",
                "",
                "",
                "",
                "",
                self.project.person_costs_incl_reservation(),
                "",
                "",
                self.total_turnover,
                self.total_loss,
            ]
        )
        yield ([])

        for budget_item in self.project.budget_items.all():
            yield (
                [
                    budget_item.description,
                    "",
                    "",
                    "",
                    "",
                    (budget_item.amount > 0) and budget_item.amount or "",
                    (budget_item.amount <= 0) and budget_item.amount_as_income() or "",
                ]
            )

        yield (["Opdrachtsom", "", "", "", "", "", self.project.contract_amount])
        yield (["Totaal", "", "", "", "", self.total_costs, self.total_income])

        yield (["Nog te verdelen", "", "", "", "", "", self.project.left_to_dish_out()])


class ProjectPersonsExcelView(ExcelResponseMixin, ProjectView):
    def has_form_permissions(self):
        return self.can_see_everything

    @property
    def excel_filename(self):
        return self.title_to_filename() + "_subsidie"

    @cached_property
    def weeks(self):
        return YearWeek.objects.filter(
            first_day__gte=self.project.start.first_day,
            first_day__lte=self.project.end.first_day,
        )

    @cached_property
    def bookings_per_week_per_person_per_project(self):
        bookings = Booking.objects.filter(year_week__in=self.weeks).values(
            "booked_by", "booked_on", "year_week").annotate(models.Sum("hours"))
        return {
            (booking["booked_by"], booking["booked_on"], booking["year_week"]): (
                booking["hours__sum"]
            )
            for booking in bookings
        }

    @property
    def prepend_lines(self):
        return [
            ["Code", self.project.code],
            ["Naam", self.project.description],
            ["Opdrachtgever", self.project.principal],
            [],
            [],
        ]

    @property
    def header_line(self):
        result = [
            "Project",
            "Omschrijving",
            "Projectleider",
            "Begindatum",
            "Einddatum",
            # 'Budget',
            # 'Besteed',
            # 'Tarief',
            # 'Omzet',
            "",
        ]
        result += [week.as_param() for week in self.weeks]
        return result

    @property
    def excel_lines(self):
        relevant_persons = self.project.assigned_persons()
        relevant_project_ids = [
            booked_on
            for (
                booked_by,
                booked_on,
                year_week,
            ) in self.bookings_per_week_per_person_per_project.keys()
        ]
        relevant_projects = Project.objects.filter(id__in=set(relevant_project_ids))
        for person in relevant_persons:
            yield [""]
            yield [""]
            yield [person]
            yield [""]
            for relevant_project in relevant_projects:
                line = [
                    relevant_project.code,
                    relevant_project.description,
                    relevant_project.project_leader,
                    relevant_project.start,
                    relevant_project.end,
                    # '',
                    # '',
                    # '',
                    # '',
                    "",
                ]
                bookings = [
                    self.bookings_per_week_per_person_per_project.get(
                        (person.id, relevant_project.id, week.id), 0
                    )
                    for week in self.weeks
                ]
                if not sum(bookings):
                    # Nothing booked on this project, omitting it.
                    continue
                line += bookings
                yield line
            totals_line = 6 * [""]
            for week in self.weeks:
                bookings = [
                    booking
                    for (
                        person_id,
                        project_id,
                        week_id,
                    ), booking in self.bookings_per_week_per_person_per_project.items()
                    if person_id == person.id and week_id == week.id
                ]
                totals_line.append(sum(bookings))
            yield totals_line


class ReservationsOverview(BaseView):
    template_name = "trs/reservations.html"

    filters_and_choices = [
        {
            "title": "Filter",
            "param": "filter",
            "default": "active",
            "choices": [
                {
                    "value": "active",
                    "title": "huidige projecten",
                    "q": Q(archived=False),
                },
                {
                    "value": "all",
                    "title": "alle projecten (inclusief archief)",
                    "q": Q(),
                },
            ],
        }
    ]

    def has_form_permissions(self):
        return self.can_see_everything

    @cached_property
    def projects(self):
        q_objects = [filter["q"] for filter in self.prepared_filters]
        return Project.objects.filter(*q_objects).filter(reservation__gt=0)

    @cached_property
    def total_reservations(self):
        return sum([project.reservation for project in self.projects])


class RatingsOverview(BaseView):
    template_name = "trs/ratings.html"

    filters_and_choices = [
        {
            "title": "Filter",
            "param": "filter",
            "default": "all",
            "choices": [
                {
                    "value": "all",
                    "title": "alle projecten (inclusief archief)",
                    "q": Q(),
                },
                {
                    "value": "active",
                    "title": "lopende projecten",
                    "q": Q(archived=False),
                },
            ],
        }
    ]

    def has_form_permissions(self):
        return self.can_see_everything

    @cached_property
    def projects(self):
        q_objects = [filter["q"] for filter in self.prepared_filters]
        at_least_one_rating = Q(rating_projectteam__gte=1) | Q(rating_customer__gte=1)
        return Project.objects.filter(*q_objects).filter(at_least_one_rating)

    @cached_property
    def average_rating_projectteam(self):
        return statistics.mean(
            [
                project.rating_projectteam
                for project in self.projects
                if project.rating_projectteam
            ]
        )

    @cached_property
    def average_rating_customer(self):
        return statistics.mean(
            [
                project.rating_customer
                for project in self.projects
                if project.rating_customer
            ]
        )


class WbsoProjectsOverview(BaseView):
    template_name = "trs/wbso_projects.html"
    title = "WBSO projecten"

    def has_form_permissions(self):
        return self.can_see_everything

    @cached_property
    def wbso_projects(self):
        return WbsoProject.objects.all()


class WbsoProjectView(BaseView):
    template_name = "trs/wbso_project.html"

    def has_form_permissions(self):
        return self.can_see_everything

    @cached_property
    def wbso_project(self):
        return WbsoProject.objects.get(pk=self.kwargs["pk"])

    @cached_property
    def projects(self):
        return self.wbso_project.projects.all()


class WbsoExcelView(ExcelResponseMixin, WbsoProjectsOverview):
    START_YEAR = 2016

    @cached_property
    def half_years(self):
        """Return half years from 1 jan START_YEAR till now.

        Also return year_week objects."""
        result = []
        years = range(self.START_YEAR, this_year_week().year + 1)
        for year in years:
            jan1 = datetime.date(year, 1, 1)
            jul1 = datetime.date(year, 7, 1)
            first_half = YearWeek.objects.filter(
                first_day__gte=jan1, first_day__lt=jul1
            ).values_list("id", flat=True)
            second_half = YearWeek.objects.filter(
                first_day__gte=jul1, year=year
            ).values_list("id", flat=True)
            result.append([f"eerste helft {year}", first_half])
            result.append([f"tweede helft {year}", second_half])
        return result

    @cached_property
    def weeks(self):
        """Return weeks from 1 jan 2014 till now."""
        start = datetime.date(2014, 1, 1)
        return YearWeek.objects.filter(
            first_day__gte=start, first_day__lt=datetime.date.today()
        )

    @cached_property
    def names_per_wbso_project_number(self):
        """Return dict of {number: name} for all WBSO projects"""
        numbers_and_names = WbsoProject.objects.all().values("number", "title")
        return {item["number"]: item["title"] for item in numbers_and_names}

    @cached_property
    def bookings_per_week_per_person_per_wbso_project(self):
        return Booking.objects.filter(
            booked_on__wbso_project__id__gt=0, year_week__in=self.weeks
        ).values(
            "booked_by__name",
            "year_week",
            "booked_on__wbso_percentage",
            "booked_on__wbso_project",
            "hours",
        )

    @property
    def prepend_lines(self):
        num_projects = len(self.found_wbso_projects)
        first_line = [""]
        for text, year_weeks in self.half_years:
            first_line.append(text)
            for i in range(num_projects - 1):
                first_line.append("")

        second_line = ["Naam"]
        for text, year_weeks in self.half_years:
            second_line += [
                self.names_per_wbso_project_number[number]
                for number in self.found_wbso_projects
            ]
        return [first_line, second_line]

    @cached_property
    def found_persons(self):
        persons = [
            item["booked_by__name"]
            for item in self.bookings_per_week_per_person_per_wbso_project
        ]
        return sorted(set(persons))

    @cached_property
    def found_wbso_projects(self):
        wbso_projects = [
            item["booked_on__wbso_project"]
            for item in self.bookings_per_week_per_person_per_wbso_project
        ]
        return list(set(wbso_projects))

    @property
    def header_line(self):
        result = ["Nummer"]
        for text, year_weeks in self.half_years:
            result += self.found_wbso_projects
        return result

    @property
    def excel_lines(self):
        for person in self.found_persons:
            line = [person]
            this_persons_bookings_per_week_per_wbso_project = [
                item
                for item in self.bookings_per_week_per_person_per_wbso_project
                if item["booked_by__name"] == person
            ]

            for text, year_weeks in self.half_years:
                for wbso_project in self.found_wbso_projects:
                    hours = [
                        round(
                            item["hours"]
                            * (item["booked_on__wbso_percentage"] or 0)
                            / 100
                        )
                        for item in this_persons_bookings_per_week_per_wbso_project
                        if item["year_week"] in year_weeks
                        and item["booked_on__wbso_project"] == wbso_project
                    ]
                    line.append(sum(hours))
            yield line


class WbsoExcelView2(ExcelResponseMixin, WbsoProjectsOverview):
    YEAR = 2023

    @cached_property
    def dates(self):
        result = []
        for month, num_of_days in enumerate(calendar.mdays):
            if month == 0:
                continue
            for day in range(num_of_days):
                result.append(datetime.date(self.YEAR, month, day + 1))
        return result

    @property
    def header_line(self):
        return ["Project", "Projectnummer"] + [
            day.strftime("%d %b") for day in self.dates
        ]

    @cached_property
    def bookings_per_week_per_wbso_project_per_person(self):
        return (
            Booking.objects.filter(
                booked_on__wbso_project__id__gt=0, year_week__year=self.YEAR
            )
            .values(
                "booked_by__name",
                "year_week__first_day",
                "booked_on__wbso_percentage",
                "booked_on__wbso_project",
                "booked_on__wbso_project__title",
            )
            .annotate(models.Sum("hours"))
        )

    # RRR

    @cached_property
    def relevant_wbso_projects(self):
        wbso_projects = set(
            [
                (
                    item["booked_on__wbso_project"],
                    item["booked_on__wbso_project__title"],
                )
                for item in self.bookings_per_week_per_wbso_project_per_person
            ]
        )
        return sorted(wbso_projects)

    @cached_property
    def relevant_persons(self):
        persons = set(
            [
                item["booked_by__name"]
                for item in self.bookings_per_week_per_wbso_project_per_person
            ]
        )
        return sorted(persons)

    def prepend_lines(self, person):
        # Different from normal prepend_lines(): we get a person as parameter.
        return [
            ["Medewerker", person],
            ["Naam en BSN-nummer"],
            ["Functie"],
            ["Jaar", self.YEAR],
            [],
        ]

    def excel_lines(self, person):
        # Different from normal excel_lines(): we get a person as parameter.

        def _wbso_hours(item):
            return round(
                item["hours__sum"] * (item["booked_on__wbso_percentage"] or 0) / 100
            )

        for wbso_project_id, wbso_project_name in self.relevant_wbso_projects:
            line = [wbso_project_name, wbso_project_id]  # TODO: uren/dag
            filled_in = {}
            bookings = [
                item
                for item in self.bookings_per_week_per_wbso_project_per_person
                if item["booked_on__wbso_project"] == wbso_project_id
                and item["booked_by__name"] == person
            ]
            for item in bookings:
                key = item["year_week__first_day"]
                existing = filled_in.get(key, 0)
                filled_in[key] = existing + _wbso_hours(item)
            for day in self.dates:
                line.append(filled_in.get(day, ""))

            yield line

    def render_to_response(self, context, **response_kwargs):
        """Return a excel response instead of a rendered template."""
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # noqa
        )
        filename = self.excel_filename + ".xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        workbook = xlsxwriter.Workbook(response)

        for person in self.relevant_persons:
            worksheet = workbook.add_worksheet(person)
            worksheet.add_write_handler(Group, _django_model_instance_to_string)
            worksheet.add_write_handler(MPC, _django_model_instance_to_string)
            worksheet.add_write_handler(Person, _django_model_instance_to_string)
            worksheet.add_write_handler(Project, _django_model_instance_to_string)

            row_number = 0
            for line in self.prepend_lines(person):
                worksheet.write_row(row_number, 0, line)
                row_number += 1  # yeah, right...
            worksheet.write_row(row_number, 0, self.header_line)
            row_number += 1
            for line in self.excel_lines(person):
                # Note: line should be a list of values.
                worksheet.write_row(row_number, 0, line)
                row_number += 1

        workbook.close()
        return response


class FinancialOverview(BaseView):
    template_name = "trs/financial_overview.html"
    title = "Overzicht financiën (als excel)"

    def has_form_permissions(self):
        return self.can_see_everything

    def download_links(self):
        yield {"name": "Gehele bedrijf", "url": reverse("trs.financial.excel")}
        yield {
            "name": "Gehele bedrijf, nieuwe gecombineerde versie",
            "url": reverse("trs.combined_financial.excel"),
        }
        for pk, name in Group.objects.all().values_list("pk", "name"):
            yield {
                "name": name,
                "url": reverse("trs.financial.excel", kwargs={"group_pk": pk}),
            }
        for pk, name in MPC.objects.all().values_list("pk", "name"):
            yield {
                "name": "MPC: " + name,
                "url": reverse("trs.financial.excel", kwargs={"mpc_pk": pk}),
            }


class FinancialExcelView(ExcelResponseMixin, ProjectsView):
    @property
    def title(self):
        return "Overzicht financien " + self.for_who

    def has_form_permissions(self):
        return self.can_see_everything

    @property
    def header_line(self):
        return [self.title]

    @cached_property
    def group(self):
        if "group_pk" in self.kwargs:
            return Group.objects.get(id=self.kwargs["group_pk"])
        return

    @cached_property
    def mpc(self):
        if "mpc_pk" in self.kwargs:
            return MPC.objects.get(id=self.kwargs["mpc_pk"])
        return

    @property
    def projects(self):
        queryset = Project.objects.filter(internal=False)
        if self.group:
            queryset = queryset.filter(group=self.group)
        if self.mpc:
            queryset = queryset.filter(mpc=self.mpc)
        return queryset

    @property
    def persons(self):
        if self.group:
            return Person.objects.filter(group=self.group)
        return Person.objects.all()

    @cached_property
    def for_who(self):
        if self.group:
            return self.group.name
        elif self.mpc:
            return self.mpc.name
        else:
            return "het gehele bedrijf"

    def _info_from_bookings(self, year):
        """Return info extracted one year's bookings"""
        # First grab the persons that booked in the year.
        relevant_person_ids = (
            Booking.objects.filter(year_week__year=year)
            .values_list("booked_by", flat=True)
            .distinct()
        )
        relevant_persons = Person.objects.filter(id__in=relevant_person_ids)
        if self.group:
            relevant_persons = relevant_persons.filter(group=self.group)
        pycs = [core.get_pyc(person=person, year=year) for person in relevant_persons]
        return {
            "turnover": sum([pyc.turnover for pyc in pycs]),
            "left_to_book_external": sum([pyc.left_to_book_external for pyc in pycs]),
            "booked_external": sum([pyc.booked_external for pyc in pycs]),
            "left_to_turn_over": sum([pyc.left_to_turn_over for pyc in pycs]),
            "overbooked_external": sum([pyc.overbooked_external for pyc in pycs]),
            "loss": sum([pyc.loss for pyc in pycs]),
        }

    @cached_property
    def info_from_bookings(self):
        """Return info extracted from this year's bookings"""
        return self._info_from_bookings(self.year)

    @cached_property
    def info_from_previous_bookings(self):
        """Return info extracted from previous year's bookings"""
        return self._info_from_bookings(self.year - 1)

    @property
    def reservations_total(self):
        return round(
            self.projects.filter(archived=False).aggregate(models.Sum("reservation"))[
                "reservation__sum"
            ]
            or 0
        )

    def invoice_table(self):
        """For this year and two years hence, return invoiced amount per month

        Per month, we need 6 values, 2 per year: the invoiced amount in that
        month plus the cumulative amount in that year till that month.

        Warning: as a side-effect, we set ``self.total_invoiced_this_year``.

        """
        years = [self.year - 2, self.year - 1, self.year]
        months = [i + 1 for i in range(12)]
        invoices = Invoice.objects.all()
        if self.group:
            invoices = invoices.filter(project__group=self.group)
        if self.mpc:
            invoices = invoices.filter(project__mpc=self.mpc)
        # For both defaultdicts, the first key is year, the second the month.
        invoiced_per_year_month = defaultdict(dict)
        cumulative_per_year_month = defaultdict(dict)
        for year in years:
            cumulative = 0
            for month in months:
                invoiced = (
                    invoices.filter(date__year=year, date__month=month).aggregate(
                        models.Sum("amount_exclusive")
                    )["amount_exclusive__sum"]
                    or 0
                )
                cumulative += invoiced
                invoiced_per_year_month[year][month] = invoiced
                cumulative_per_year_month[year][month] = cumulative

        yield ["", "", self.year - 2, "", self.year - 1, "", self.year]
        for month, month_name in enumerate(MONTHS, start=1):
            row = ["", month_name]
            for year in years:
                row.append(invoiced_per_year_month[year][month])
                row.append(cumulative_per_year_month[year][month])
            yield row

        totals = ["", "Totaal"]
        for year in years:
            totals.append(cumulative_per_year_month[year][12])
            totals.append("")
        yield totals

        # A bit hacky to set it here...
        self.total_invoiced_this_year = cumulative_per_year_month[self.year][12]

    def confirmed_amount_table(self):
        """Return contract amounts for confirmed projects per year/month.

        Per month, we need 6 values, 2 per year: the contract amount in that
        month plus the cumulative amount in that year till that month.

        """
        years = [self.year - 2, self.year - 1, self.year]
        months = [i + 1 for i in range(12)]
        # For both defaultdicts, the first key is year, the second the month.
        confirmed_amount_per_year_month = defaultdict(dict)
        cumulative_per_year_month = defaultdict(dict)
        for year in years:
            cumulative = 0
            for month in months:
                confirmed_amount = (
                    self.projects.filter(
                        confirmation_date__year=year, confirmation_date__month=month
                    ).aggregate(models.Sum("contract_amount"))["contract_amount__sum"]
                    or 0
                )
                cumulative += confirmed_amount
                confirmed_amount_per_year_month[year][month] = confirmed_amount
                cumulative_per_year_month[year][month] = cumulative

        yield ["", "", self.year - 2, "", self.year - 1, "", self.year]
        for month, month_name in enumerate(MONTHS, start=1):
            row = ["", month_name]
            for year in years:
                row.append(confirmed_amount_per_year_month[year][month])
                row.append(cumulative_per_year_month[year][month])
            yield row

        totals = ["", "Totaal"]
        for year in years:
            totals.append(cumulative_per_year_month[year][12])
            totals.append("")
        yield totals

    @property
    def total_payables(self):
        """Return sum of payables ('kosten derden') with a date of this year"""
        return (
            Payable.objects.filter(
                project__in=self.projects, date__year=self.year
            ).aggregate(models.Sum("amount"))["amount__sum"]
            or 0
        )

    @cached_property
    def target(self):
        if self.group:
            return self.group.target
        elif self.mpc:
            return self.mpc.target
        else:
            # The target of the whole company is the sum of all groups'
            # targets.
            # TODO: this doesn't match MPC's, really
            return Group.objects.all().aggregate(models.Sum("target"))["target__sum"]

    @cached_property
    def project_counts(self):
        """Return counts like 'new in 2016' for projects"""
        result = {}
        active_projects = self.projects.filter(archived=False)
        result["active"] = active_projects.count()

        confirmed_projects = active_projects.exclude(confirmation_date__isnull=True)
        result["with_confirmation"] = confirmed_projects.count()

        ended_projects = active_projects.filter(end__lt=this_year_week())
        result["ended"] = ended_projects.count()

        offered_projects = active_projects.filter(
            confirmation_date__isnull=True
        ).exclude(bid_send_date__isnull=False)
        result["offered"] = offered_projects.count()

        to_estimate_projects = active_projects.filter(
            confirmation_date__isnull=True
        ).exclude(bid_send_date__isnull=True)
        result["to_estimate"] = to_estimate_projects.count()

        unconfirmed_projects = active_projects.filter(confirmation_date__isnull=True)
        booked_without_confirmation = Booking.objects.filter(
            booked_on__in=unconfirmed_projects
        ).aggregate(models.Sum("hours"))["hours__sum"]
        result["booked_without_confirmation"] = booked_without_confirmation
        # Offerte-uren zonder opdracht
        return result

    def fte(self):
        """Return number of FTEs"""
        persons = self.persons.filter(archived=False).prefetch_related("person_changes")
        total_hours_per_week = sum([person.hours_per_week() for person in persons])
        return round(total_hours_per_week / 40.0, 1)

    def sick_days(self):
        """Return number of booked sick days"""
        sickness_projects = Project.objects.filter(description="Ziekte").filter(
            archived=False
        )
        if not sickness_projects:
            return "Geen project met naam 'Ziekte' gevonden"

        sick_hours = Booking.objects.filter(
            booked_by__in=self.persons,
            booked_on__in=sickness_projects,
            year_week__year=self.year,
        ).aggregate(models.Sum("hours"))["hours__sum"]

        if not sick_hours:
            return 0
        return round(sick_hours / 8)

    def days_to_book(self):
        persons = self.persons.filter(archived=False).prefetch_related("bookings")
        hours_to_book = sum([person.to_book()["hours"] for person in persons])
        return round(hours_to_book / 8)

    @property
    def excel_lines(self):
        yield ["", "Datum uitdraai:", self.today.strftime("%d-%m-%Y")]
        yield ["", "Voor:", self.for_who]
        yield []
        yield ["1. GEREALISEERDE OMZET"]
        yield []
        yield ["", "", "Uren", "Geld", "", "Uren vorig jaar", "Geld vorig jaar"]
        yield [
            "",
            "Gerealiseerde omzet dit jaar",
            self.info_from_bookings["booked_external"],
            self.info_from_bookings["turnover"],
            "",
            self.info_from_previous_bookings["booked_external"],
            self.info_from_previous_bookings["turnover"],
        ]
        yield [
            "",
            "Werkvoorraad",
            self.info_from_bookings["left_to_book_external"],
            self.info_from_bookings["left_to_turn_over"],
            "",
            self.info_from_previous_bookings["left_to_book_external"],
            self.info_from_previous_bookings["left_to_turn_over"],
        ]
        yield ["", "Totaal reserveringen", "", self.reservations_total]
        yield [
            "",
            "Verliesuren dit jaar",
            self.info_from_bookings["overbooked_external"],
            self.info_from_bookings["loss"],
            "",
            self.info_from_previous_bookings["overbooked_external"],
            self.info_from_previous_bookings["loss"],
        ]
        yield []
        yield ["2. GEFACTUREERDE OMZET"]
        yield []
        for row in self.invoice_table():
            yield row
        yield []
        yield ["", "Gefactureerde omzet dit jaar", self.total_invoiced_this_year]
        yield ["", "Kosten derden", self.total_payables]
        yield ["", "Omzetdoelstelling", self.target]
        yield [
            "",
            "Verschil voor dit jaar",
            (self.total_invoiced_this_year - self.total_payables - self.target),
        ]
        yield []
        yield ["3. OPDRACHTEN"]
        yield []
        for row in self.confirmed_amount_table():
            yield row
        yield []
        yield ["", "Aantal projecten", self.project_counts["active"]]
        yield ["", "Al geeindigd", self.project_counts["ended"]]
        yield ["", "Projecten met opdracht", self.project_counts["with_confirmation"]]
        yield ["", "In offerte stadium", self.project_counts["offered"]]
        yield ["", "Nog te begroten", self.project_counts["to_estimate"]]
        yield []
        yield [
            "",
            "(Offerte-)uren zonder opdracht",
            self.project_counts["booked_without_confirmation"],
        ]
        yield []
        yield ["4. OVERIG"]
        yield []
        yield ["", "Aantal FTE", self.fte()]
        yield ["", "Aantal dagen ziekteverlof", self.sick_days()]
        yield ["", "Dagen achter met boeken", self.days_to_book()]


class PayablesExcelView(ExcelResponseMixin, PayablesView):
    header_line = [
        "Factuurdatum",
        "Factuurnummer",
        "Groep",
        "MPC",
        "Project",
        "Gearchiveerd",
        "Opdrachtgever",
        "Omschrijving",
        "Bedrag",
        "Betaald",
    ]

    @property
    def excel_lines(self):
        for payable in self.payables:
            line = [
                payable.date,
                payable.number,
                payable.project.group,
                payable.project.mpc,
                payable.project.code,
                payable.project.archived,
                payable.project.principal,
                payable.description,
                payable.amount,
                payable.payed,
            ]
            yield line


class CombinedFinancialExcelView(ExcelResponseMixin, ProjectsView):
    title = "Gecombineerd overzicht financien"

    def has_form_permissions(self):
        return self.can_see_everything

    @property
    def external_projects(self):
        return Project.objects.filter(internal=False)

    @property
    def header_line(self):
        return ["", self.title]

    @cached_property
    def groups(self):
        # Exclude groups with a `(`, those are the non-active ones.
        return list(Group.objects.exclude(name__contains="("))

    @cached_property
    def group_names_incl_total(self):
        return [TOTAL_COMPANY] + [group.name for group in self.groups]

    def _info_from_bookings(self, year=None, group=None):
        """Return info extracted one year's bookings"""
        if year is None:
            year = self.year
        # First grab the persons that booked in the year.
        relevant_person_ids = (
            Booking.objects.filter(year_week__year=year)
            .values_list("booked_by", flat=True)
            .distinct()
        )
        relevant_persons = Person.objects.filter(id__in=relevant_person_ids)
        if group:
            relevant_persons = relevant_persons.filter(group=group)
        pycs = [core.get_pyc(person=person, year=year) for person in relevant_persons]
        return {
            "turnover": sum([pyc.turnover for pyc in pycs]),
            "left_to_book_external": sum([pyc.left_to_book_external for pyc in pycs]),
            "booked_external": sum([pyc.booked_external for pyc in pycs]),
            "left_to_turn_over": sum([pyc.left_to_turn_over for pyc in pycs]),
            "overbooked_external": sum([pyc.overbooked_external for pyc in pycs]),
            "loss": sum([pyc.loss for pyc in pycs]),
        }

    def reservations_total(self, group=None):
        relevant_projects = self.external_projects.filter(archived=False)
        if group:
            relevant_projects = relevant_projects.filter(group=group)
        return round(
            relevant_projects.aggregate(models.Sum("reservation"))["reservation__sum"]
            or 0
        )

    def costs_total(self, group=None):
        # Note: combination of budget_item and budget_transfer.
        relevant_projects = self.external_projects.filter(archived=False)
        if group:
            relevant_projects = relevant_projects.filter(group=group)
        costs = round(
            relevant_projects.aggregate(models.Sum("budget_items__amount"))[
                "budget_items__amount__sum"
            ]
            or 0
        )
        income = round(
            relevant_projects.aggregate(models.Sum("budget_transfers__amount"))[
                "budget_transfers__amount__sum"
            ]
            or 0
        )
        return costs - income

    def software_development_total(self, group=None):
        relevant_projects = self.external_projects.filter(archived=False)
        if group:
            relevant_projects = relevant_projects.filter(group=group)
        return round(
            relevant_projects.aggregate(models.Sum("software_development"))[
                "software_development__sum"
            ]
            or 0
        )

    def profit_total(self, group=None):
        relevant_projects = self.external_projects.filter(archived=False)
        if group:
            relevant_projects = relevant_projects.filter(group=group)
        return round(
            relevant_projects.aggregate(models.Sum("profit"))["profit__sum"] or 0
        )

    def _invoice_table(self, group=None):
        """For this year and two years hence, return invoiced amount per month

        Per month, we need 6 values, 2 per year: the invoiced amount in that
        month plus the cumulative amount in that year till that month.

        Warning: as a side-effect, we set ``self.total_invoiced_this_year``.

        """
        years = [self.year - 2, self.year - 1, self.year]
        months = [i + 1 for i in range(12)]
        invoices = Invoice.objects.all()
        if group:
            invoices = invoices.filter(project__group=group)
        # For both defaultdicts, the first key is year, the second the month.
        invoiced_per_year_month = defaultdict(dict)
        cumulative_per_year_month = defaultdict(dict)
        for year in years:
            cumulative = 0
            for month in months:
                invoiced = (
                    invoices.filter(date__year=year, date__month=month).aggregate(
                        models.Sum("amount_exclusive")
                    )["amount_exclusive__sum"]
                    or 0
                )
                cumulative += invoiced
                invoiced_per_year_month[year][month] = invoiced
                cumulative_per_year_month[year][month] = cumulative

        totals = {}
        for year in years:
            totals[year] = cumulative_per_year_month[year][12]

        return {
            "invoiced_per_year_month": invoiced_per_year_month,
            "cumulative_per_year_month": cumulative_per_year_month,
            "totals": totals,
        }

    def _confirmed_amount_table(self, group=None):
        """Return contract amounts for confirmed projects per year/month.

        Per month, we need 6 values, 2 per year: the contract amount in that
        month plus the cumulative amount in that year till that month.

        """
        years = [self.year - 2, self.year - 1, self.year]
        months = [i + 1 for i in range(12)]
        # For both defaultdicts, the first key is year, the second the month.
        confirmed_amount_per_year_month = defaultdict(dict)
        cumulative_per_year_month = defaultdict(dict)
        projects = self.external_projects
        if group:
            projects = projects.filter(group=group)
        for year in years:
            cumulative = 0
            for month in months:
                confirmed_amount = (
                    projects.filter(
                        confirmation_date__year=year, confirmation_date__month=month
                    ).aggregate(models.Sum("contract_amount"))["contract_amount__sum"]
                    or 0
                )
                cumulative += confirmed_amount
                confirmed_amount_per_year_month[year][month] = confirmed_amount
                cumulative_per_year_month[year][month] = cumulative

        totals = {}
        for year in years:
            totals[year] = cumulative_per_year_month[year][12]
        return {
            "confirmed_amount_per_year_month": confirmed_amount_per_year_month,
            "cumulative_per_year_month": cumulative_per_year_month,
            "totals": totals,
        }

    def total_payables_this_year(self, group=None):
        """Return sum of payables ('kosten derden') with a date of this year"""
        payables = Payable.objects.filter(date__year=self.year)
        if group:
            payables = payables.filter(project__group=group)
        return payables.aggregate(models.Sum("amount"))["amount__sum"] or 0

    def target(self, group=None):
        if group:
            return group.target
        else:
            # The target of the whole company is the sum of all groups'
            # targets.
            return Group.objects.all().aggregate(models.Sum("target"))["target__sum"]

    def _project_counts(self, group=None):
        """Return counts like 'new in 2016' for projects"""
        result = {}
        projects = self.external_projects
        if group:
            projects = projects.filter(group=group)
        active_projects = projects.filter(archived=False)
        result["active"] = active_projects.count()

        confirmed_projects = active_projects.exclude(confirmation_date__isnull=True)
        result["with_confirmation"] = confirmed_projects.count()

        ended_projects = active_projects.filter(end__lt=this_year_week())
        result["ended"] = ended_projects.count()

        offered_projects = active_projects.filter(
            confirmation_date__isnull=True
        ).exclude(bid_send_date__isnull=False)
        result["offered"] = offered_projects.count()

        to_estimate_projects = active_projects.filter(
            confirmation_date__isnull=True
        ).exclude(bid_send_date__isnull=True)
        result["to_estimate"] = to_estimate_projects.count()

        unconfirmed_projects = active_projects.filter(confirmation_date__isnull=True)
        booked_without_confirmation = (
            Booking.objects.filter(booked_on__in=unconfirmed_projects).aggregate(
                models.Sum("hours")
            )["hours__sum"]
            or 0
        )
        result["booked_without_confirmation"] = booked_without_confirmation
        # Offerte-uren zonder opdracht
        return result

    def _person_counts(self, group=None):
        """Return counts like 'fte' and 'sick days'"""
        result = {}
        persons = (
            Person.objects.filter(archived=False)
            .prefetch_related("person_changes")
            .prefetch_related("bookings")
        )
        if group:
            persons = persons.filter(group=group)
        total_hours_per_week = sum([person.hours_per_week() for person in persons])
        result["fte"] = round(total_hours_per_week / 40.0, 1)

        sickness_projects = Project.objects.filter(description="Ziekte").filter(
            archived=False
        )
        if sickness_projects:
            sick_hours = (
                Booking.objects.filter(
                    booked_by__in=persons,
                    booked_on__in=sickness_projects,
                    year_week__year=self.year,
                ).aggregate(models.Sum("hours"))["hours__sum"]
                or 0
            )
            result["sick_days"] = round(sick_hours / 8)
        else:
            logger.warn("Geen project met naam 'Ziekte' gevonden")
            result["sick_days"] = 0

        result["days_to_book"] = round(
            sum([person.to_book()["hours"] for person in persons]) / 8
        )
        return result

    @property
    def excel_lines(self):
        yield [
            "",
            "Datum uitdraai:",
            self.today.strftime("%d-%m-%Y"),
            "Weeknummer:",
            this_year_week().week,
        ]
        line = ["", "Kostenplaats:", "Totaal", "", "", "", ""]
        for name in self.group_names_incl_total:
            line += [name, "", ""]
        yield line

        yield []
        line = ["1.", "GEREALISEERDE OMZET", "", "", (self.year - 1), "", ""]
        for i in range(len(self.group_names_incl_total)):
            line += [self.year, "", ""]
        yield line

        line = ["", "", "", ""]
        for i in range(len(self.group_names_incl_total)):
            line += ["Uren", "Euro", ""]
        yield line

        info_from_previous_bookings = self._info_from_bookings(year=self.year - 1)
        info_from_bookings = {}
        info_from_bookings[TOTAL_COMPANY] = self._info_from_bookings()
        for group in self.groups:
            info_from_bookings[group.name] = self._info_from_bookings(group=group)

        for title, key1, key2 in [
            ["Gerealiseerde omzet (uur*tarief)", "booked_external", "turnover"],
            ["Werkvoorraad", "left_to_book_external", "left_to_turn_over"],
            ["Verliesuren", "overbooked_external", "loss"],
        ]:
            line = [
                "",
                title,
                "",
                "",
                info_from_previous_bookings[key1],
                info_from_previous_bookings[key2],
                "",
            ]
            for name in self.group_names_incl_total:
                line += [
                    info_from_bookings[name][key1],
                    info_from_bookings[name][key2],
                    "",
                ]
            yield line

        line = [
            "",
            "Totaal reserveringen",
            "",
            "",
            "",
            "",
            "",
            "",
            self.reservations_total(group=None),
            "",
        ]
        for group in self.groups:
            line += ["", self.reservations_total(group=group), ""]
        yield line
        line = [
            "",
            "Overige kosten",
            "",
            "",
            "",
            "",
            "",
            "",
            self.costs_total(group=None),
            "",
        ]
        for group in self.groups:
            line += ["", self.costs_total(group=group), ""]
        yield line
        line = [
            "",
            "Software ontwikkeling",
            "",
            "",
            "",
            "",
            "",
            "",
            self.software_development_total(group=None),
            "",
        ]
        for group in self.groups:
            line += ["", self.software_development_total(group=group), ""]
        yield line
        line = [
            "",
            "Afdracht",
            "",
            "",
            "",
            "",
            "",
            "",
            self.profit_total(group=None),
            "",
        ]
        for group in self.groups:
            line += ["", self.profit_total(group=group), ""]
        yield line

        days_elapsed = datetime.date.today().timetuple().tm_yday
        portion_of_year = days_elapsed / 365
        year_percentage = round(portion_of_year * 100)

        targets = {}  # Also used by "2. GEFACTUREERDE OMZET" en "3. OPDRACHTEN".
        targets[TOTAL_COMPANY] = self.target()
        for group in self.groups:
            targets[group.name] = self.target(group=group)
        person_counts = {}  # ALso used by "4. OVERIG".
        person_counts[TOTAL_COMPANY] = self._person_counts()
        for group in self.groups:
            person_counts[group.name] = self._person_counts(group=group)

        fte = {name: person_counts[name]["fte"] for name in self.group_names_incl_total}
        targets_per_fte = {
            key: (fte[key] and round(float(value) / fte[key]) or 0)
            for (key, value) in targets.items()
        }
        targets_per_fte_relative = {
            key: round(value * portion_of_year)
            for (key, value) in targets_per_fte.items()
        }
        realized_turnover_per_fte = {
            name: (
                fte[name]
                and round(info_from_bookings[name]["turnover"] / fte[name])
                or 0
            )
            for name in self.group_names_incl_total
        }
        realized_relative = {
            key: (value and round(realized_turnover_per_fte[key] / value * 100) or 0)
            for (key, value) in targets_per_fte_relative.items()
        }

        yield []
        for title, info in [
            ["Omzetdoelstelling/fte (jaar)", targets_per_fte],
            [
                f"Omzetdoelstelling/fte ({year_percentage}% jaar)",
                targets_per_fte_relative,
            ],
            ["Gerealiseerde omzet/fte (tot nu toe)", realized_turnover_per_fte],
            ["Gerealiseerde omzet/fte (% tot nu toe)", realized_relative],
        ]:
            line = ["", title, "", "", "", ""]
            for name in self.group_names_incl_total:
                line += ["", "", info[name]]
            yield line
        yield []

        line = [
            "2.",
            "GEFACTUREERDE OMZET",
            (self.year - 2),
            "",
            (self.year - 1),
            "",
            "",
        ]
        for i in range(len(self.group_names_incl_total)):
            line += [self.year, "", ""]
        yield line

        invoice_table = {}
        invoice_table[TOTAL_COMPANY] = self._invoice_table()
        for group in self.groups:
            invoice_table[group.name] = self._invoice_table(group=group)
        for month, month_name in enumerate(MONTHS, start=1):
            line = [
                "",
                month_name,
                invoice_table[TOTAL_COMPANY]["invoiced_per_year_month"][self.year - 2][
                    month
                ],
                invoice_table[TOTAL_COMPANY]["cumulative_per_year_month"][
                    self.year - 2
                ][month],
                invoice_table[TOTAL_COMPANY]["invoiced_per_year_month"][self.year - 1][
                    month
                ],
                invoice_table[TOTAL_COMPANY]["cumulative_per_year_month"][
                    self.year - 1
                ][month],
            ]
            for name in self.group_names_incl_total:
                line += [
                    "",
                    invoice_table[name]["invoiced_per_year_month"][self.year][month],
                    invoice_table[name]["cumulative_per_year_month"][self.year][month],
                ]
            yield line

        line = [
            "",
            "Totaal",
            invoice_table[TOTAL_COMPANY]["totals"][self.year - 2],
            "",
            invoice_table[TOTAL_COMPANY]["totals"][self.year - 1],
            "",
        ]
        for name in self.group_names_incl_total:
            line += ["", invoice_table[name]["totals"][self.year], ""]
        yield line

        yield []
        totals = {}
        total_payables = {}
        differences = {}
        totals[TOTAL_COMPANY] = invoice_table[TOTAL_COMPANY]["totals"][self.year]
        total_payables[TOTAL_COMPANY] = self.total_payables_this_year()
        differences[TOTAL_COMPANY] = (
            totals[TOTAL_COMPANY]
            - total_payables[TOTAL_COMPANY]
            - targets[TOTAL_COMPANY]
        )
        for group in self.groups:
            totals[group.name] = invoice_table[group.name]["totals"][self.year]
            total_payables[group.name] = self.total_payables_this_year(group=group)
            differences[group.name] = (
                totals[group.name] - total_payables[group.name] - targets[group.name]
            )
        for title, info in [
            ["Gefactureerde omzet dit jaar", totals],
            ["Kosten derden", total_payables],
            ["Omzetdoelstelling", targets],
            ["Verschil voor dit jaar", differences],
        ]:
            line = ["", title, "", "", "", ""]
            for name in self.group_names_incl_total:
                line += ["", info[name], ""]
            yield line

        yield []
        line = [
            "3.",
            "OPDRACHTEN (verkoop)",
            (self.year - 2),
            "",
            (self.year - 1),
            "",
            "",
        ]
        for i in range(len(self.group_names_incl_total)):
            line += [self.year, "", ""]
        yield line
        confirmed_amount_table = {}
        confirmed_amount_table[TOTAL_COMPANY] = self._confirmed_amount_table()
        for group in self.groups:
            confirmed_amount_table[group.name] = self._confirmed_amount_table(
                group=group
            )
        for month, month_name in enumerate(MONTHS, start=1):
            line = [
                "",
                month_name,
                confirmed_amount_table[TOTAL_COMPANY][
                    "confirmed_amount_per_year_month"
                ][self.year - 2][month],
                confirmed_amount_table[TOTAL_COMPANY]["cumulative_per_year_month"][
                    self.year - 2
                ][month],
                confirmed_amount_table[TOTAL_COMPANY][
                    "confirmed_amount_per_year_month"
                ][self.year - 1][month],
                confirmed_amount_table[TOTAL_COMPANY]["cumulative_per_year_month"][
                    self.year - 1
                ][month],
            ]
            for name in self.group_names_incl_total:
                line += [
                    "",
                    confirmed_amount_table[name]["confirmed_amount_per_year_month"][
                        self.year
                    ][month],
                    confirmed_amount_table[name]["cumulative_per_year_month"][
                        self.year
                    ][month],
                ]
            yield line

        line = [
            "",
            "Totaal",
            confirmed_amount_table[TOTAL_COMPANY]["totals"][self.year - 2],
            "",
            confirmed_amount_table[TOTAL_COMPANY]["totals"][self.year - 1],
            "",
        ]
        for name in self.group_names_incl_total:
            line += ["", confirmed_amount_table[name]["totals"][self.year], ""]
        yield line

        yield []
        sell_targets = {
            key: round(float(value) * 1.1) for (key, value) in targets.items()
        }
        sell_targets_relative = {
            key: round(value * portion_of_year) for (key, value) in sell_targets.items()
        }
        realized_relative = {
            key: (
                value
                and round(
                    confirmed_amount_table[key]["totals"][self.year] / value * 100
                )
                or 0
            )
            for (key, value) in sell_targets_relative.items()
        }
        for title, info in [
            ["Verkoopdoelstelling (jaar)", sell_targets],
            [
                f"Verkoopdoelstelling ({year_percentage}% jaar)",
                sell_targets_relative,
            ],
            ["Gerealiseerde verkoop (% tot nu toe)", realized_relative],
        ]:
            line = ["", title, "", "", "", ""]
            for name in self.group_names_incl_total:
                line += ["", info[name], ""]
            yield line

        project_counts = {}
        project_counts[TOTAL_COMPANY] = self._project_counts()
        for group in self.groups:
            project_counts[group.name] = self._project_counts(group=group)

        yield []
        for title, key in [
            ["Aantal projecten", "active"],
            ["Al geëindigd", "ended"],
            ["Projecten met opdracht", "with_confirmation"],
            ["In offertestadium", "offered"],
            ["Nog te begroten", "to_estimate"],
            ["(Offerte-)uren zonder opdracht", "booked_without_confirmation"],
        ]:
            line = ["", title, "", "", "", ""]
            for name in self.group_names_incl_total:
                line += ["", project_counts[name][key], ""]
            yield line

        yield []
        line = ["4.", "OVERIG", "", "", "", "", ""]
        for i in range(len(self.group_names_incl_total)):
            line += [self.year, "", ""]
        yield line

        yield []
        for title, key in [
            ["Aantal FTE", "fte"],
            ["Aantal dagen ziekteverlof", "sick_days"],
            ["Dagen achter met boeken", "days_to_book"],
        ]:
            line = ["", title, "", "", "", ""]
            for name in self.group_names_incl_total:
                line += ["", person_counts[name][key], ""]
            yield line
