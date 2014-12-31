from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
import csv
import datetime
import logging
import time
import urllib

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.datastructures import SortedDict
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView

from trs import core
from trs.models import Booking
from trs.models import BudgetItem
from trs.models import Group
from trs.models import Invoice
from trs.models import Person
from trs.models import PersonChange
from trs.models import Project
from trs.models import WorkAssignment
from trs.models import YearWeek
from trs.models import this_year_week
from trs.templatetags.trs_formatting import hours as format_as_hours
from trs.templatetags.trs_formatting import money as format_as_money


logger = logging.getLogger(__name__)

BIG_PROJECT_SIZE = 200  # hours
MAX_BAR_HEIGHT = 50  # px
BAR_WIDTH = 75  # px
BACK_TEMPLATE = '<div><small><a href="{url}">&larr; {text}</a></small></div>'


class LoginAndPermissionsRequiredMixin(object):
    """See http://stackoverflow.com/a/10304880/27401"""

    def has_form_permissions(self):
        """Especially for forms, return whether we have the necessary perms.

        Overwrite this in subclasses.
        """
        return True

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.has_form_permissions():
            raise PermissionDenied
        return super(LoginAndPermissionsRequiredMixin,
                     self).dispatch(*args, **kwargs)


def try_and_find_matching_person(user):
    full_name = user.first_name + ' ' + user.last_name
    full_name = full_name.lower()
    full_name = full_name.replace(',', ' ')
    full_name = full_name.replace('-', ' ')
    parts = full_name.split(' ')
    names = Person.objects.all().values_list('name', flat=True)
    for part in parts:
        names = [name for name in names if part in name.lower()]
    if len(names) > 1:
        logger.warn("Tried matching %s, but found more than one match: %s",
                    full_name, names)
        return
    if len(names) == 1:
        return Person.objects.get(name=names[0])


def home(request):
    return redirect('trs.booking')


class BaseMixin(object):
    template_name = 'trs/base.html'
    title = "TRS tijdregistratiesysteem"
    filters_and_choices = []
    normally_visible_filters = None

    @cached_property
    def current_get_params(self):
        params = {}
        for filter in self.prepared_filters:
            if filter['active']:
                params[filter['param']] = filter['active_value']

        return urllib.parse.urlencode(params)

    @cached_property
    def prepared_filters(self):
        filters = deepcopy(self.filters_and_choices)

        # Figure out which params are at non-default values
        non_default_params = {}
        for filter in filters:
            param = filter['param']
            from_get = self.request.GET.get(param, None)
            if from_get is None:
                continue
            if from_get == filter['default']:
                continue
            allowed_values = [choice['value'] for choice in filter['choices']]
            if from_get not in allowed_values:
                continue
            non_default_params[param] = from_get

        # Calculate query string for choices and determine active choices.
        # Also add queries for the database.
        for filter in filters:
            param = filter['param']
            get_params = deepcopy(non_default_params)
            filter['active'] = (param in get_params)
            if self.normally_visible_filters is None:
                filter['hidden'] = False
            else:
                filter['hidden'] = not (param in self.normally_visible_filters
                                        or filter['active'])
            active_value = get_params.get(param, filter['default'])
            filter['active_value'] = active_value
            for choice in filter['choices']:
                get_params[param] = choice['value']
                choice['query_string'] = urllib.parse.urlencode(get_params)
                choice['active'] = (choice['value'] == active_value)
                if choice['active']:
                    filter['q'] = choice['q']

        return filters

    @cached_property
    def filters(self):
        # BBB version of prepared_filters()
        return {filter['param']: filter['active_value']
                for filter in self.prepared_filters}

    @cached_property
    def today(self):
        return datetime.date.today()

    @cached_property
    def year(self):
        # Customization based on year happens a lot.
        return int(self.request.GET.get('year', this_year_week().year))

    @cached_property
    def is_custom_year(self):
        return self.year != this_year_week().year

    @cached_property
    def active_person(self):
        if self.request.user.is_anonymous():
            logger.debug("Anonymous user")
            return
        persons = Person.objects.filter(user=self.request.user)
        if not persons:
            logger.warn("Person matching request's user %s not found.",
                        self.request.user)
            # Try to couple based on username. One-time action. This means you
            # can prepare persons beforehand and have them automatically
            # coupled the moment they sign in. A real automatic LDAP coupling
            # would have been better, but python-ldap doesn't work with python
            # 3 yet.
            person = try_and_find_matching_person(self.request.user)
            if person:
                logger.info("Found not-yet-coupled person %s for user %s.",
                            person, self.request.user)
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
    def selected_tab(self):
        recognized = ['booking', 'projects', 'persons', 'overviews']
        for path_element in recognized:
            path_start = '/%s/' % path_element
            if self.request.path.startswith(path_start):
                return path_element

    @cached_property
    def admin_override_active(self):
        # Allow an admin to see everything for debug purposes.
        if self.request.user.is_superuser:
            if 'admin_override_active' not in self.request.session:
                self.request.session['admin_override_active'] = False
            if 'all' in self.request.GET:
                self.request.session['admin_override_active'] = True
            if 'notall' in self.request.GET:
                self.request.session['admin_override_active'] = False
            if self.request.session['admin_override_active']:
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
        if not hasattr(self, 'project'):
            return False
        if self.can_edit_and_see_everything:
            return True
        if self.active_person in [self.project.project_manager,
                                  self.project.project_leader]:
            return True

    @cached_property
    def gauges_id(self):
        return getattr(settings, 'GAUGES_ID', None)

    @cached_property
    def group_choices(self):
        return list(Group.objects.all().values_list('pk', 'name'))


class BaseView(LoginAndPermissionsRequiredMixin, TemplateView, BaseMixin):
    pass


class PersonsView(BaseView):

    title = "Medewerkers"

    @cached_property
    def filters_and_choices(self):
        result = [
            {'title': 'Status',
             'param': 'status',
             'default': 'active',
             'choices': [
                 {'value': 'active',
                  'title': 'huidige medewerkers',
                  'q': Q(archived=False)},
                 {'value': 'archived',
                  'title': 'gearchiveerde medewerkers',
                  'q': Q(archived=True)},
             ]},
            {'title': 'Groep',
             'param': 'group',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'Geen filter',
                  'q': Q()}] +
             [{'value': str(group.id),
               'title': group.name,
               'q': Q(group=group.id)}
              for group in Group.objects.all()] +
             [{'value': 'geen',
               'title': 'Zonder groep',
               'q': Q(group=None)}]},
        ]
        return result

    @property
    def template_name(self):
        if self.can_view_elaborate_version:
            return 'trs/persons.html'
        return 'trs/persons-simple.html'

    @cached_property
    def can_view_elaborate_version(self):
        if self.can_see_everything:
            return True

    @cached_property
    def can_add_person(self):
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def persons(self):
        q_objects = [filter['q'] for filter in self.prepared_filters]
        return Person.objects.filter(*q_objects)

    @cached_property
    def lines(self):
        return [{'person': person, 'pyc': core.get_pyc(person)}
                for person in self.persons]

    @cached_property
    def total_turnover(self):
        return sum([line['pyc'].turnover for line in self.lines])

    @cached_property
    def total_left_to_book(self):
        return sum([line['pyc'].left_to_book_external for line in self.lines])

    @cached_property
    def total_left_to_turn_over(self):
        return sum([line['pyc'].left_to_turn_over for line in self.lines])


class PersonView(BaseView):
    template_name = 'trs/person.html'

    filters_and_choices = [
        {'title': 'Filter',
         'param': 'filter',
         'default': 'active',
         'choices': [
             {'value': 'active',
              'title': 'huidige projecten',
              'q': Q(archived=False)},
             {'value': 'all',
              'title': 'alle projecten (inclusief archief)',
              'q': Q()},
         ]},
    ]

    @cached_property
    def person(self):
        return Person.objects.get(pk=self.kwargs['pk'])

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
        q_objects = [filter['q'] for filter in self.prepared_filters]
        return self.person.assigned_projects().filter(*q_objects)

    @cached_property
    def projects(self):
        if self.can_see_internal_projects:
            return self.all_projects
        return [project for project in self.all_projects
                if not project.internal]

    @cached_property
    def lines(self):
        """Return project info per line"""
        # TODO: somewhat similar to BookingView.
        result = []
        # Budget query.
        budget_per_project = WorkAssignment.objects.filter(
            assigned_to=self.person,
            assigned_on__in=self.projects).values(
                'assigned_on').annotate(
                    models.Sum('hours'),
                    models.Sum('hourly_tariff'))
        budgets = {
            item['assigned_on']: round(item['hours__sum'] or 0)
            for item in budget_per_project}
        hourly_tariffs = {
            item['assigned_on']: round(item['hourly_tariff__sum'] or 0)
            for item in budget_per_project}
        # Hours worked query.
        booked_per_project = Booking.objects.filter(
            booked_by=self.person,
            booked_on__in=self.projects).values(
                'booked_on').annotate(
                    models.Sum('hours'))
        booked_this_year_per_project = Booking.objects.filter(
            booked_by=self.person,
            booked_on__in=self.projects,
            year_week__year=this_year_week().year).values(
                'booked_on').annotate(
                    models.Sum('hours'))
        booked = {item['booked_on']: round(item['hours__sum'] or 0)
                  for item in booked_per_project}
        booked_this_year = {item['booked_on']: round(item['hours__sum'] or 0)
                            for item in booked_this_year_per_project}

        for project in self.projects:
            line = {'project': project}
            line['budget'] = budgets.get(project.id, 0)
            line['booked'] = booked.get(project.id, 0)
            line['booked_this_year'] = booked_this_year.get(project.id, 0)
            line['booked_previous_years'] = (line['booked'] -
                                             line['booked_this_year'])
            line['is_overbooked'] = line['booked'] > line['budget']
            line['left_to_book'] = max(0, line['budget'] - line['booked'])
            line['is_project_leader'] = (
                project.project_leader_id == self.person.id)
            line['is_project_manager'] = (
                project.project_manager_id == self.person.id)
            line['hourly_tariff'] = hourly_tariffs.get(project.id, 0)
            line['turnover'] = (
                min(line['budget'],
                    line['booked']) * line['hourly_tariff'])
            result.append(line)
        return result

    @cached_property
    def extra_roles(self):
        num_project_leader_roles = sum(
            [project.project_leader_id == self.person.id
             for project in self.all_projects])
        num_project_manager_roles = sum(
            [project.project_manager_id == self.person.id
             for project in self.all_projects])
        roles = []
        if num_project_leader_roles:
            roles.append("%s keer projectleider" % num_project_leader_roles)
        if num_project_manager_roles:
            roles.append("%s keer projectmanager" % num_project_manager_roles)
        if self.person.is_management:
            roles.append("in management")
        if self.person.is_office_management:
            roles.append("in office management")
        if not roles:
            return 'Geen'
        return ', '.join(roles)


class PersonKPIView(PersonView):
    template_name = 'trs/kpi.html'

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
            line['project'] = project
            result.append(line)
        return result

    @cached_property
    def available_years(self):
        years_person_booked_in = list(Booking.objects.filter(
            booked_by=self.sidebar_person).values(
                'year_week__year').distinct().values_list(
                    'year_week__year', flat=True))
        current_year = this_year_week().year
        if current_year not in years_person_booked_in:
            # Corner case if you haven't booked yet in this year :-)
            years_person_booked_in.append(current_year)
        return years_person_booked_in


class BookingOverview(PersonView):
    template_name = 'trs/booking_overview.html'

    def has_form_permissions(self):
        if self.can_see_everything:
            return True
        if self.active_person == self.person:
            return True
        return False

    @cached_property
    def year(self):
        return int(self.request.GET.get('year', this_year_week().year))

    @cached_property
    def available_years(self):
        years_i_booked_in = list(Booking.objects.filter(
            booked_by=self.person).values(
                'year_week__year').distinct().values_list(
                    'year_week__year', flat=True))
        current_year = this_year_week().year
        if current_year not in years_i_booked_in:
            # Corner case if you haven't booked yet in this year :-)
            years_i_booked_in.append(current_year)
        return years_i_booked_in

    @cached_property
    def lines(self):
        booked_this_year_per_week = Booking.objects.filter(
            booked_by=self.person,
            year_week__year=self.year).values(
                'year_week__week').annotate(
                    models.Sum('hours'))
        booked_per_week = {
            item['year_week__week']: round(item['hours__sum'] or 0)
            for item in booked_this_year_per_week}
        start_hours_amount = round(self.person.person_changes.filter(
            year_week__year__lt=self.year).aggregate(
                models.Sum('hours_per_week'))['hours_per_week__sum'] or 0)
        changes_this_year = self.person.person_changes.filter(
            year_week__year=self.year).values(
                'year_week__week').annotate(
                    models.Sum('hours_per_week'))
        changes_per_week = {change['year_week__week']:
                            round(change['hours_per_week__sum'])
                            for change in changes_this_year}
        result = []
        to_book = start_hours_amount
        for year_week in YearWeek.objects.filter(year=self.year):
            to_book += changes_per_week.get(year_week.week, 0)
            to_book_this_week = to_book - year_week.num_days_missing * 8
            # num_days_missing is only relevant for the first and last week of
            # a year.
            booked = booked_per_week.get(year_week.week, 0)
            klass = ''
            hint = ''
            if booked < to_book_this_week:
                klass = 'danger'
                hint = "Te boeken: %s" % round(to_book_this_week)
            if (year_week.year == this_year_week().year and
                year_week.week >= this_year_week().week):
                # Don't complain about this or future weeks.
                klass = ''
            result.append({'year_week': year_week,
                           'booked': booked,
                           'klass': klass,
                           'hint': hint})
        return result


class ProjectsView(BaseView):

    @cached_property
    def filters_and_choices(self):
        result = [
            {'title': 'Status',
             'param': 'status',
             'default': 'active',
             'choices': [
                 {'value': 'active',
                  'title': 'huidige projecten',
                  'q': Q(archived=False)},
                 {'value': 'archived',
                  'title': 'gearchiveerde projecten',
                  'q': Q(archived=True)},
             ]},

            {'title': 'Subsidie',
             'param': 'is_subsidized',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'Geen filter',
                  'q': Q()},
                 {'value': 'false',
                  'title': 'geen subsidie',
                  'q': Q(is_subsidized=False)},
                 {'value': 'true',
                  'title': 'subsidieprojecten',
                  'q': Q(is_subsidized=True)},
             ]},

            {'title': 'Geaccepteerd',
             'param': 'is_accepted',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'Geen filter',
                  'q': Q()},
                 {'value': 'false',
                  'title': 'niet',
                  'q': Q(is_accepted=False)},
                 {'value': 'true',
                  'title': 'wel',
                  'q': Q(is_accepted=True)},
             ]},

            {'title': 'Startoverleg',
             'param': 'startup_meeting_done',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'Geen filter',
                  'q': Q()},
                 {'value': 'false',
                  'title': 'nog niet',
                  'q': Q(is_accepted=False)},
                 {'value': 'true',
                  'title': 'wel gehouden',
                  'q': Q(is_accepted=True)},
             ]},

            {'title': 'Groep',
             'param': 'group',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'Geen filter',
                  'q': Q()}] +
             [{'value': str(group.id),
               'title': group.name,
               'q': Q(group=group.id)}
              for group in Group.objects.all()] +
             [{'value': 'geen',
               'title': 'Zonder groep',
               'q': Q(group=None)}]},

            {'title': 'Projectleider',
             'param': 'project_leader',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'Geen filter',
                  'q': Q()}] +
             [{'value': str(person.id),
               'title': person.name,
               'q': Q(project_leader=person.id)}
              for person in self.project_leaders] +
             [{'value': 'geen',
               'title': 'zonder PL',
               'q': Q(project_leader=None)}]},

            {'title': 'Projectmanager',
             'param': 'project_manager',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'Geen filter',
                  'q': Q()}] +
             [{'value': str(person.id),
               'title': person.name,
               'q': Q(project_manager=person.id)}
              for person in self.project_managers] +
             [{'value': 'geen',
               'title': 'zonder PM',
               'q': Q(project_manager=None)}]},

            {'title': 'Al gestart',
             'param': 'started',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'Geen filter',
                  'q': Q()},
                 {'value': 'true',
                  'title': 'ja',
                  'q': Q(start__lte=this_year_week())},
                 {'value': 'false',
                  'title': 'nee',
                  'q': Q(start__gt=this_year_week())}]},

            {'title': 'Al geeindigd',
             'param': 'ended',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'Geen filter',
                  'q': Q()},
                 {'value': 'true',
                  'title': 'ja',
                  'q': Q(end__lt=this_year_week())},
                 {'value': 'false',
                  'title': 'nee',
                  'q': Q(end__gte=this_year_week())}]},

        ]
        return result

    @cached_property
    def normally_visible_filters(self):
        result = ['status',
                  'group']
        if self.can_see_everything:
            result += [
                'is_subsidized',
                'is_accepted',
                'startup_meeting_done',
                'started',
                'ended',
                ]
        # Chicken/egg problem.
        if ('project_leader' in self.request.GET or
            'project_manager' in self.request.GET):
            result += [
                'project_leader',
                'project_manager',
            ]
        return result

    title = "Projecten"

    @cached_property
    def project_leaders(self):
        return Person.objects.filter(
            projects_i_lead__archived=False).distinct()

    @cached_property
    def project_managers(self):
        return Person.objects.filter(
            projects_i_manage__archived=False).distinct()

    @property
    def template_name(self):
        if self.can_view_elaborate_version:
            return 'trs/projects.html'
        return 'trs/projects-simple.html'

    @cached_property
    def can_add_project(self):
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def can_view_elaborate_version(self):
        if self.can_see_everything:
            return True
        if self.filters['project_leader']:
            if self.filters['project_leader'] == self.active_person.id:
                return True
        if self.filters['project_manager']:
            if self.filters['project_manager'] == self.active_person.id:
                return True

    @cached_property
    def projects(self):
        q_objects = [filter['q'] for filter in self.prepared_filters]
        result = Project.objects.filter(*q_objects)
        if not self.can_view_elaborate_version:
            result = result.filter(hidden=False)

        # Pagination, mostly for the looooooong archive projects list.
        page = self.request.GET.get('page')
        paginator = Paginator(result, 500)
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
        invoices_per_project = Invoice.objects.filter(
            project__in=self.projects).values(
                'project').annotate(
                    models.Sum('amount_exclusive')).order_by()
        # ^^^ .order_by() is needed to prevent a weird grouping issue. See
        # https://docs.djangoproject.com/en/1.6/topics/db/aggregation/
        # #interaction-with-default-ordering-or-order-by
        invoice_amounts = {item['project']: item['amount_exclusive__sum']
                           for item in invoices_per_project}

        for project in self.projects:
            line = {}
            line['project'] = project
            if project.overbooked_percentage() > 50:
                klass = 'danger'
            elif project.overbooked_percentage():
                klass = 'warning'
            else:
                klass = 'default'
            line['klass'] = klass
            invoice_amount = invoice_amounts.get(project.id, 0)
            turnover = project.turnover()
            costs = project.costs()
            income = project.income()
            reservation = project.reservation
            if project.contract_amount:
                invoice_amount_percentage = round(
                    invoice_amount / project.contract_amount * 100)
            else:  # Division by zero.
                invoice_amount_percentage = None
            if turnover + costs + reservation - income:
                invoice_versus_turnover_percentage = round(
                    invoice_amount / (turnover + costs + reservation - income) * 100)
            else:
                invoice_versus_turnover_percentage = None
            line['contract_amount'] = project.contract_amount
            line['invoice_amount'] = invoice_amount
            line['turnover'] = turnover
            line['person_costs_incl_reservation'] = (project.person_costs() +
                                                     project.reservation)
            line['reservation'] = project.reservation
            line['other_costs'] = costs - income
            line['invoice_amount_percentage'] = invoice_amount_percentage
            line['invoice_versus_turnover_percentage'] = (
                invoice_versus_turnover_percentage)
            result.append(line)
        return result

    @cached_property
    def totals(self):
        return {key: sum([line[key] for line in self.lines]) or 0
                for key in ['turnover', 'person_costs_incl_reservation', 'reservation',
                            'other_costs']}

    @cached_property
    def total_invoice_amount_percentage(self):
        result = {}
        result['contract_amount'] = sum([line['contract_amount']
                                         for line in self.lines])
        result['invoice_amount'] = sum([line['invoice_amount']
                                        for line in self.lines])
        if result['contract_amount']:
            percentage = round(
                result['invoice_amount'] / result['contract_amount'] * 100)
        else:  # Division by zero.
            percentage = None
        result['percentage'] = percentage
        return result


class ProjectView(BaseView):
    template_name = 'trs/project.html'

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['pk'])

    @cached_property
    def title(self):
        return "Project %s: %s" % (self.project.code, self.project.description)

    @cached_property
    def can_view_team(self):
        if not self.project.hidden:
            # Normally everyone can see it.
            return True
        if self.is_project_management:
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
    def can_edit_team(self):
        if self.project.archived:
            return False
        if self.is_project_management:
            return True

    @cached_property
    def can_see_financials(self):
        if self.is_project_management:
            return True
        if self.active_person in self.project.assigned_persons():
            return True

    @cached_property
    def can_see_project_financials(self):
        if self.is_project_management:
            return True

    @cached_property
    def lines(self):
        result = []
        # Budget query.
        budget_per_person = WorkAssignment.objects.filter(
            assigned_to__in=self.persons,
            assigned_on=self.project).values(
                'assigned_to').annotate(
                    models.Sum('hours'),
                    models.Sum('hourly_tariff'))
        budgets = {
            item['assigned_to']: round(item['hours__sum'] or 0)
            for item in budget_per_person}
        hourly_tariffs = {
            item['assigned_to']: round(item['hourly_tariff__sum'] or 0)
            for item in budget_per_person}
        # Hours worked query.
        booked_per_person = Booking.objects.filter(
            booked_by__in=self.persons,
            booked_on=self.project).values(
                'booked_by').annotate(
                    models.Sum('hours'))
        booked = {item['booked_by']: round(item['hours__sum'] or 0)
                  for item in booked_per_person}

        for person in self.persons:
            line = {'person': person}
            line['budget'] = budgets.get(person.id, 0)
            line['booked'] = booked.get(person.id, 0)
            line['is_overbooked'] = line['booked'] > line['budget']
            line['left_to_book'] = max(0, line['budget'] - line['booked'])
            line['is_project_leader'] = (
                self.project.project_leader_id == person.id)
            line['is_project_manager'] = (
                self.project.project_manager_id == person.id)
            line['hourly_tariff'] = hourly_tariffs.get(person.id, 0)
            tariff = line['hourly_tariff']
            line['turnover'] = (
                min(line['budget'], line['booked']) * tariff)
            line['loss'] = (
                max(0, (line['booked'] - line['budget'])) * tariff)
            line['left_to_turn_over'] = line['left_to_book'] * tariff
            line['planned_turnover'] = line['budget'] * tariff
            line['desired_hourly_tariff'] = round(
                person.standard_hourly_tariff(year_week=self.project.start))
            result.append(line)
        return result

    @cached_property
    def persons(self):
        return self.project.assigned_persons()

    @cached_property
    def total_turnover(self):
        return sum([line['turnover'] for line in self.lines])

    @cached_property
    def total_loss(self):
        return sum([line['loss'] for line in self.lines])

    @cached_property
    def total_turnover_left(self):
        return sum([line['left_to_turn_over'] for line in self.lines])

    @cached_property
    def person_costs_incl_reservation(self):
        person_costs = sum([line['planned_turnover'] for line in self.lines])
        return person_costs + self.project.reservation

    @cached_property
    def total_costs(self):
        return self.project.costs() + self.person_costs_incl_reservation

    @cached_property
    def total_income(self):
        return self.project.contract_amount + self.project.income()

    @cached_property
    def amount_left(self):
        return self.subtotal - self.total_turnover - self.total_turnover_left

    @cached_property
    def total_invoice_exclusive(self):
        return sum([invoice.amount_exclusive
                    for invoice in self.project.invoices.all()])

    @cached_property
    def total_invoice_inclusive(self):
        return sum([invoice.amount_inclusive
                    for invoice in self.project.invoices.all()])


class LoginView(FormView, BaseMixin):
    template_name = 'trs/login.html'
    form_class = AuthenticationForm

    @cached_property
    def success_url(self):
        return reverse('trs.booking')

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super(LoginView, self).form_valid(form)


def logout_view(request):
    logout(request)
    return redirect('trs.home')


class BookingView(LoginAndPermissionsRequiredMixin, FormView, BaseMixin):
    template_name = 'trs/booking.html'

    def has_form_permissions(self):
        # Warning: this is permission to view the page, not directly
        # permission to edit someone else's bookings.
        if self.can_see_everything:
            return True
        return self.active_person == self.person

    @cached_property
    def person(self):
        person_id = self.kwargs.get('pk')
        if person_id is None:
            return self.active_person
        return Person.objects.get(pk=person_id)

    @cached_property
    def title(self):
        if self.active_person != self.person:
            return "Boekingen van %s" % self.person
        return "Uren boeken"

    @cached_property
    def sidebar_person(self):
        if self.can_see_everything:
            return self.person
        if self.person == self.active_person:
            return self.person

    @cached_property
    def active_year_week(self):
        year = self.kwargs.get('year')
        week = self.kwargs.get('week')
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
        result = list(YearWeek.objects.filter(first_day__lte=end).filter(
            first_day__gte=start))
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
            start__lte=latest_week).distinct()

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
        fields = SortedDict()
        if (self.person == self.active_person):
            # If not, we cannot edit anything, just view.
            for index, project in enumerate(self.relevant_projects):
                field_type = forms.IntegerField(
                    min_value=0,
                    max_value=100,
                    widget=forms.TextInput(attrs={'size': 2,
                                                  'tabindex': index + 1}))
                fields[project.code] = field_type
        return type("GeneratedBookingForm", (forms.Form,), fields)

    @cached_property
    def initial(self):
        """Return initial form values.

        Turn the decimals into integers already."""
        result = {}
        bookings = Booking.objects.filter(
            year_week=self.active_year_week,
            booked_by=self.person,
            booked_on__in=self.relevant_projects).values(
                'booked_on__code').annotate(
                    models.Sum('hours'))
        result = {item['booked_on__code']: round(item['hours__sum'] or 0)
                  for item in bookings}
        return {project.code: result.get(project.code, 0)
                for project in self.relevant_projects}

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
                project = [project for project in self.relevant_projects
                           if project.code == project_code][0]
                booking = Booking(hours=difference,
                                  booked_by=self.person,
                                  booked_on=project,
                                  year_week=self.active_year_week)
                booking.save()

        if absolute_difference:
            if total_difference < 0:
                indicator = total_difference
            elif total_difference > 0:
                indicator = '+%s' % total_difference
            else:  # 0
                indicator = "alleen verschoven"
            messages.success(self.request, "Uren aangepast (%s)." % indicator)
        else:
            messages.info(self.request, "Niets aan de uren gewijzigd.")
        elapsed = (time.time() - start_time)
        logger.debug("Handled booking in %s secs", elapsed)
        return super(BookingView, self).form_valid(form)

    @cached_property
    def tabindex_submit_button(self):
        return len(self.relevant_projects) + 1

    @cached_property
    def success_url(self):
        return reverse('trs.booking', kwargs={
            'pk': self.person.id,
            'year': self.active_year_week.year,
            'week': self.active_year_week.week})

    @cached_property
    def lines(self):
        """Return project plus a set of four hours."""
        result = []
        form = self.get_form(self.get_form_class())
        fields = list(form)  # A form's __iter__ returns 'bound fields'.
        # Prepare booking info as one query.
        booking_table = Booking.objects.filter(
            year_week__in=self.year_weeks_to_display,
            booked_by=self.person).values(
                'booked_on', 'year_week').annotate(
                    models.Sum('hours'))
        bookings = {(item['booked_on'], item['year_week']):
                    item['hours__sum'] or 0
                    for item in booking_table}
        # Idem for budget
        budget_per_project = WorkAssignment.objects.filter(
            assigned_to=self.person,
            assigned_on__in=self.relevant_projects).values(
                'assigned_on').annotate(
                    models.Sum('hours'))
        budgets = {item['assigned_on']: round(item['hours__sum'] or 0)
                   for item in budget_per_project}
        # Item for hours worked.
        booked_per_project = Booking.objects.filter(
            booked_by=self.person,
            booked_on__in=self.relevant_projects).values(
                'booked_on').annotate(
                    models.Sum('hours'))
        booked_total = {item['booked_on']: round(item['hours__sum'] or 0)
                        for item in booked_per_project}

        this_year = this_year_week().year
        for project_index, project in enumerate(self.relevant_projects):
            line = {'project': project}
            for index, year_week in enumerate(self.year_weeks_to_display):
                booked = bookings.get((project.id, year_week.id), 0)
                key = 'hours%s' % index
                line[key] = booked

            if fields:
                line['field'] = fields[project_index]
                if (project.archived or
                    project.start > self.active_year_week or
                    project.end < self.active_year_week or
                    self.active_year_week.year < this_year):
                    # Filtering if we're allowed to book or not.
                    line['field'].field.widget.attrs['hidden'] = True
                    line['show_uneditable_value'] = True
            else:
                # No fields: we're only allowed to view the data, not edit it.
                line['field'] = ''
                line['show_uneditable_value'] = True

            line['budget'] = budgets.get(project.id, 0)
            line['booked_total'] = booked_total.get(project.id, 0)
            line['is_overbooked'] = line['booked_total'] > line['budget']
            line['left_to_book'] = max(
                0, line['budget'] - line['booked_total'])
            result.append(line)
        return result

    def totals(self):
        return [sum([line['hours%s' % index] for line in self.lines])
                for index in range(4)]


class ProjectEditView(LoginAndPermissionsRequiredMixin,
                      UpdateView,
                      BaseMixin):
    template_name = 'trs/edit.html'
    model = Project

    @property
    def fields(self):
        if self.can_edit_and_see_everything:
            return ['code', 'description', 'group',
                    'internal', 'hidden', 'hourless',
                    'archived',  # Note: archived only on edit view :-)
                    'is_subsidized', 'principal',
                    'contract_amount',
                    'start', 'end', 'project_leader', 'project_manager',
                    # Note: the next two are shown only on the edit view!
                    'startup_meeting_done', 'is_accepted',
                    'remark', 'financial_remark',
                    'end',
                    ]
        result = ['remark', 'financial_remark', 'start', 'end']
        if self.active_person == self.project.project_leader:
            if not self.project.startup_meeting_done:
                result.append('startup_meeting_done')
        if self.active_person == self.project.project_manager:
            if not self.project.is_accepted:
                result.append('is_accepted')
        return result

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['pk'])

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
        return super(ProjectEditView, self).form_valid(form)


class ProjectCreateView(LoginAndPermissionsRequiredMixin,
                        CreateView,
                        BaseMixin):
    template_name = 'trs/create-project.html'
    model = Project
    title = "Nieuw project"
    fields = ['code', 'description', 'group', 'internal', 'hidden', 'hourless',
              'is_subsidized', 'principal',
              'contract_amount',
              'start', 'end', 'project_leader', 'project_manager',
              'remark', 'financial_remark',
    ]

    def has_form_permissions(self):
        if self.can_edit_and_see_everything:
            return True

    def form_valid(self, form):
        messages.success(self.request, "Project aangemaakt")
        return super(ProjectCreateView, self).form_valid(form)

    def latest_projects(self):
        # Note: they're reverse sorted, so we want the first :-)
        external = Project.objects.filter(internal=False,
                                          archived=False)[:3]
        internal = Project.objects.filter(internal=True,
                                          archived=False)[:3]
        return list(external) + list(internal)


class InvoiceCreateView(LoginAndPermissionsRequiredMixin,
                        CreateView,
                        BaseMixin):
    template_name = 'trs/edit.html'
    model = Invoice
    title = "Nieuwe factuur"
    fields = ['date', 'number', 'description',
              'amount_exclusive', 'vat', 'payed']

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['project_pk'])

    @cached_property
    def success_url(self):
        return reverse('trs.project', kwargs={'pk': self.project.pk})

    def form_valid(self, form):
        form.instance.project = self.project
        messages.success(self.request, "Factuur toegevoegd")
        return super(InvoiceCreateView, self).form_valid(form)


class InvoiceEditView(LoginAndPermissionsRequiredMixin,
                      UpdateView,
                      BaseMixin):
    template_name = 'trs/edit-invoice.html'
    model = Invoice
    fields = ['date', 'number', 'description',
              'amount_exclusive', 'vat', 'payed']

    @property
    def title(self):
        return "Aanpassen factuur voor %s" % self.project.code

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['project_pk'])

    @cached_property
    def invoice(self):
        return Invoice.objects.get(pk=self.kwargs['pk'])

    def edit_action(self):
        if 'from_invoice_overview' in self.request.GET:
            return '.?from_invoice_overview'

    @cached_property
    def success_url(self):
        if 'from_invoice_overview' in self.request.GET:
            params = '?year=%s#%s' % (self.invoice.date.year, self.invoice.id)
            return reverse('trs.overviews.invoices') + params
        return reverse('trs.project', kwargs={'pk': self.project.pk})

    def form_valid(self, form):
        messages.success(self.request, "Factuur aangepast")
        return super(InvoiceEditView, self).form_valid(form)


class BudgetItemCreateView(LoginAndPermissionsRequiredMixin,
                           CreateView,
                           BaseMixin):
    template_name = 'trs/edit.html'
    model = BudgetItem
    title = "Nieuw begrotingsitem"
    fields = ['description', 'amount', 'to_project']

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.is_project_management:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['project_pk'])

    @cached_property
    def success_url(self):
        return reverse('trs.project', kwargs={'pk': self.project.pk})

    def form_valid(self, form):
        form.instance.project = self.project
        messages.success(self.request, "Begrotingsitem toegevoegd")
        return super(BudgetItemCreateView, self).form_valid(form)


class BudgetItemEditView(LoginAndPermissionsRequiredMixin,
                         UpdateView,
                         BaseMixin):
    template_name = 'trs/edit.html'
    model = BudgetItem
    fields = ['description', 'amount', 'to_project']

    @property
    def title(self):
        return "Aanpassen begrotingsitem voor %s" % self.project.code

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.is_project_management:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['project_pk'])

    @cached_property
    def success_url(self):
        return reverse('trs.project', kwargs={'pk': self.project.pk})

    def form_valid(self, form):
        messages.success(self.request, "Begrotingsitem aangepast")
        return super(BudgetItemEditView, self).form_valid(form)


class PersonEditView(LoginAndPermissionsRequiredMixin,
                     UpdateView,
                     BaseMixin):
    template_name = 'trs/edit.html'
    model = Person
    fields = ['name', 'user', 'group', 'is_management', 'archived']

    @cached_property
    def person(self):
        return Person.objects.get(pk=self.kwargs['pk'])

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
        return super(PersonEditView, self).form_valid(form)


class PersonCreateView(LoginAndPermissionsRequiredMixin,
                       CreateView,
                       BaseMixin):
    template_name = 'trs/edit.html'
    model = Person
    title = "Nieuwe medewerker"
    fields = ['name', 'user', 'group', 'is_management']

    def has_form_permissions(self):
        if self.can_edit_and_see_everything:
            return True

    def form_valid(self, form):
        messages.success(self.request, "Medewerker aangemaakt")
        return super(PersonCreateView, self).form_valid(form)


class TeamUpdateView(LoginAndPermissionsRequiredMixin, FormView, BaseMixin):
    """View for auto-adding internal members (if needed)."""
    template_name = 'trs/team-update.html'

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['pk'])

    @cached_property
    def title(self):
        return "Projectteam updaten voor %s" % self.project.code

    form_class = forms.Form  # Yes, an empty form.

    @cached_property
    def missing_internal_persons(self):
        if self.project.internal:
            already_assigned = self.project.assigned_persons()
            active_persons = Person.objects.filter(archived=False)
            missing = [person for person in active_persons
                       if person not in already_assigned]
            return missing
        return []

    def form_valid(self, form):
        num_added = 0
        for person in self.missing_internal_persons:
            WorkAssignment.objects.get_or_create(
                assigned_on=self.project,
                assigned_to=person)
            num_added += 1
        messages.success(self.request, "%s teamleden toegevoegd" % num_added)
        return super(TeamUpdateView, self).form_valid(form)

    @cached_property
    def success_url(self):
        return reverse('trs.project.team', kwargs={'pk': self.project.pk})

    @cached_property
    def back_url(self):
        url = self.project.get_absolute_url()
        text = "Terug naar het project"
        return mark_safe(BACK_TEMPLATE.format(url=url, text=text))


class DeleteView(LoginAndPermissionsRequiredMixin, FormView, BaseMixin):
    template_name = 'trs/delete.html'

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['pk'])

    form_class = forms.Form  # Yes, an empty form.

    @cached_property
    def back_url(self):
        url = self.project.get_absolute_url()
        text = "Terug naar het project"
        return mark_safe(BACK_TEMPLATE.format(url=url, text=text))


class TeamMemberDeleteView(DeleteView):

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True
        if self.person_has_booked:
            return False

    @cached_property
    def person(self):
        return Person.objects.get(pk=self.kwargs['person_pk'])

    @cached_property
    def person_has_booked(self):
        return Booking.objects.filter(
            booked_on=self.project,
            booked_by=self.person).exists()

    @cached_property
    def title(self):
        return "Verwijder %s uit %s" % (self.person.name, self.project.code)

    def form_valid(self, form):
        WorkAssignment.objects.filter(
            assigned_on=self.project,
            assigned_to=self.person).delete()
        self.project.save()  # Increment cache key.
        self.person.save()  # Increment cache key.
        messages.success(
            self.request,
            "%s verwijderd uit %s" % (self.person.name, self.project.code))
        return super(TeamMemberDeleteView, self).form_valid(form)

    @cached_property
    def success_url(self):
        return reverse('trs.project.team', kwargs={'pk': self.project.pk})


class BudgetItemDeleteView(DeleteView):

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.is_project_management:
            return True

    @cached_property
    def budget_item(self):
        return BudgetItem.objects.get(pk=self.kwargs['budget_item_pk'])

    @cached_property
    def title(self):
        return "Verwijder budget item %s uit %s" % (
            self.budget_item.description, self.project.code)

    def form_valid(self, form):
        self.budget_item.delete()
        self.project.save()  # Increment cache key.
        messages.success(
            self.request,
            "%s verwijderd uit %s" % (self.budget_item.description,
                                      self.project.code))
        return super(BudgetItemDeleteView, self).form_valid(form)

    @cached_property
    def success_url(self):
        return reverse('trs.project', kwargs={'pk': self.project.pk})


class InvoiceDeleteView(DeleteView):

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def invoice(self):
        return Invoice.objects.get(pk=self.kwargs['invoice_pk'])

    @cached_property
    def title(self):
        return "Verwijder factuur %s uit %s" % (self.invoice.number,
                                                self.project.code)

    def form_valid(self, form):
        self.invoice.delete()
        self.project.save()  # Increment cache key.
        messages.success(
            self.request,
            "%s verwijderd uit %s" % (self.invoice.number, self.project.code))
        return super(InvoiceDeleteView, self).form_valid(form)

    @cached_property
    def success_url(self):
        return reverse('trs.project', kwargs={'pk': self.project.pk})


class TeamEditView(LoginAndPermissionsRequiredMixin, FormView, BaseMixin):
    template_name = 'trs/team.html'

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.is_project_management:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['pk'])

    @cached_property
    def title(self):
        return "Personele kosten voor %s bewerken" % self.project.code

    @cached_property
    def can_edit_hours(self):
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True

    @cached_property
    def can_add_team_member(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True

    @property
    def can_delete_team_member(self):
        # Note: team members can in any case only be deleted if they haven't
        # yet booked any hours on the project.
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True

    @cached_property
    def can_edit_hourly_tariff(self):
        if self.is_project_management:
            return True

    def hours_fieldname(self, person):
        return 'hours-%s' % person.id

    def hourly_tariff_fieldname(self, person):
        return 'hourly_tariff-%s' % person.id

    @cached_property
    def budgets_and_tariffs(self):
        budget_per_person = WorkAssignment.objects.filter(
            assigned_on=self.project).values(
                'assigned_to').annotate(
                    models.Sum('hours'),
                    models.Sum('hourly_tariff'))
        budgets = {
            item['assigned_to']: round(item['hours__sum'] or 0)
            for item in budget_per_person}
        hourly_tariffs = {
            item['assigned_to']: round(item['hourly_tariff__sum'] or 0)
            for item in budget_per_person}
        return budgets, hourly_tariffs

    def get_form_class(self):
        """Return dynamically generated form class."""
        fields = SortedDict()
        tabindex = 1
        budgets, hourly_tariffs = self.budgets_and_tariffs

        # WorkAssignment fields
        for index, person in enumerate(self.project.assigned_persons()):
            if person.archived:
                continue
            if self.can_edit_hours:
                field_type = forms.IntegerField(
                    min_value=0,
                    initial=round(budgets.get(person.id, 0)),
                    widget=forms.TextInput(attrs={'size': 4,
                                                  'tabindex': tabindex}))
                fields[self.hours_fieldname(person)] = field_type
                tabindex += 1
            if self.can_edit_hourly_tariff:
                field_type = forms.IntegerField(
                    min_value=0,
                    initial=round(hourly_tariffs.get(person.id, 0)),
                    widget=forms.TextInput(attrs={'size': 4,
                                                  'tabindex': tabindex}))
                fields[self.hourly_tariff_fieldname(person)] = field_type
                tabindex += 1

        # Reservation field
        fields['reservation'] = forms.IntegerField(
            min_value=0,
            initial=int(self.project.reservation),
            widget=forms.TextInput(attrs={'size': 4,
                                          'tabindex': tabindex}))
        tabindex += 1

        if self.can_add_team_member:
            # New team member field
            name = 'new_team_member'
            choices = list(Person.objects.filter(
                archived=False).values_list('pk', 'name'))
            choices.insert(0, ('', '---'))
            field_type = forms.ChoiceField(
                required=False,
                choices=choices,
                widget=forms.Select(attrs={'tabindex': tabindex}))
            fields[name] = field_type
            tabindex += 1

        return type("GeneratedTeamEditForm", (forms.Form,), fields)

    @cached_property
    def bound_form_fields(self):
        form = self.get_form(self.get_form_class())
        return list(form)

    @cached_property
    def lines(self):
        result = []
        fields = self.bound_form_fields
        field_index = 0
        budgets, hourly_tariffs = self.budgets_and_tariffs
        booked_per_person = Booking.objects.filter(
            booked_on=self.project).values(
                'booked_by').annotate(
                    models.Sum('hours'))
        booked = {item['booked_by']: round(item['hours__sum'] or 0)
                  for item in booked_per_person}
        for person in self.project.assigned_persons():
            line = {'person': person}
            if self.can_edit_hours and not person.archived:
                line['hours'] = fields[field_index]
                field_index += 1
            else:
                line['hours'] = format_as_hours(budgets.get(person.id, 0))
            if self.can_edit_hourly_tariff and not person.archived:
                line['hourly_tariff'] = fields[field_index]
                field_index += 1
            else:
                line['hourly_tariff'] = format_as_money(
                    hourly_tariffs.get(person.id, 0))
            line['booked'] = format_as_hours(booked.get(person.id, 0))
            line['costs'] = (hourly_tariffs.get(person.id, 0) *
                             budgets.get(person.id, 0))
            line['deletable'] = False
            if not booked.get(person.id):
                if self.can_delete_team_member:
                    line['deletable'] = True
            result.append(line)
        return result

    @cached_property
    def new_team_member_field(self):
        if self.can_add_team_member:
            return self.bound_form_fields[-1]

    @cached_property
    def reservation_field(self):
        if self.can_add_team_member:
            return self.bound_form_fields[-2]
        else:
            return self.bound_form_fields[-1]

    def form_valid(self, form):
        num_changes = 0
        budgets, hourly_tariffs = self.budgets_and_tariffs
        for person in self.project.assigned_persons():
            if person.archived:
                continue
            hours = 0
            hourly_tariff = 0
            if self.can_edit_hours:
                current = round(budgets.get(person.id, 0))
                new = form.cleaned_data.get(self.hours_fieldname(person))
                hours = new - current
            if self.can_edit_hourly_tariff:
                current = round(hourly_tariffs.get(person.id, 0))
                new = form.cleaned_data.get(
                    self.hourly_tariff_fieldname(person))
                hourly_tariff = new - current
            if hours or hourly_tariff:
                num_changes += 1
                work_assignment = WorkAssignment(
                    hours=hours,
                    hourly_tariff=hourly_tariff,
                    assigned_on=self.project,
                    assigned_to=person)
                work_assignment.save()
                logger.info("Added work assignment")
        if num_changes:
            messages.success(self.request,
                             "Teamleden: %s gewijzigd" % num_changes)

        reservation = form.cleaned_data.get('reservation')
        if self.project.reservation != reservation:
            self.project.reservation = reservation
            self.project.save()
            msg = "Reservering is op %s gezet" % reservation
            messages.success(self.request, msg)

        if self.can_add_team_member:
            new_team_member_id = form.cleaned_data.get('new_team_member')
            if new_team_member_id:
                person = Person.objects.get(id=new_team_member_id)
                msg = "%s is aan het team toegevoegd" % person.name
                work_assignment = WorkAssignment(
                    assigned_on=self.project,
                    assigned_to=person)
                work_assignment.save()
                logger.info(msg)
                messages.success(self.request, msg)

        return super(TeamEditView, self).form_valid(form)

    @cached_property
    def person_costs_incl_reservation(self):
        person_costs = sum([line['costs'] for line in self.lines])
        return person_costs + self.project.reservation

    @cached_property
    def total_costs(self):
        return self.project.costs() + self.person_costs_incl_reservation

    @cached_property
    def total_income(self):
        return self.project.contract_amount + self.project.income()

    @cached_property
    def success_url(self):
        return reverse('trs.project.team', kwargs={'pk': self.project.pk})

    @cached_property
    def back_url(self):
        url = self.project.get_absolute_url()
        text = "Terug naar het project"
        return mark_safe(BACK_TEMPLATE.format(url=url, text=text))


class PersonChangeView(LoginAndPermissionsRequiredMixin,
                       CreateView,
                       BaseMixin):
    template_name = 'trs/person-change.html'
    model = PersonChange
    fields = ['hours_per_week', 'target', 'standard_hourly_tariff',
              'minimum_hourly_tariff']

    def has_form_permissions(self):
        if self.person.archived:
            return False
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def person(self):
        return Person.objects.get(pk=self.kwargs['pk'])

    @cached_property
    def title(self):
        return "Wijzig gegevens voor %s (stand %s)" % (
            self.person.name, self.chosen_year_week)

    @cached_property
    def success_url(self):
        return self.person.get_absolute_url()

    @cached_property
    def edit_action(self):
        return '.?year_week=%s' % self.chosen_year_week.as_param()

    @cached_property
    def chosen_year_week(self):
        if 'year_week' not in self.request.GET:
            # Return the current week, unless we're at the start of the year.
            if this_year_week().week < 5:
                return YearWeek.objects.filter(
                    year=this_year_week().year).first()
            else:
                return this_year_week()
        year, week = self.request.GET['year_week'].split('-')
        return YearWeek.objects.get(year=int(year), week=int(week))

    def year_week_suggestions(self):
        current_year = this_year_week().year
        next_year = current_year + 1
        return [
            # (yyyy-ww, title)
            (YearWeek.objects.filter(year=current_year).first().as_param(),
             'Begin %s (begin dit jaar)' % current_year),
            (this_year_week().as_param(),
             'Nu'),
            (YearWeek.objects.filter(year=next_year).first().as_param(),
             'Begin %s (begin volgend jaar)' % next_year),
        ]

    def all_year_weeks(self):
        # Well, all... 2013 is our TRS start year.
        return YearWeek.objects.filter(year__gte=2013)

    @cached_property
    def previous_changes(self):
        changes = list(PersonChange.objects.filter(
            person=self.person).values(
                'year_week').annotate(
                    models.Sum('hours_per_week'),
                    models.Sum('target'),
                    models.Sum('standard_hourly_tariff'),
                    models.Sum('minimum_hourly_tariff')))
        relevant_weeks = YearWeek.objects.filter(
            id__in=[change['year_week'] for change in changes])
        for index, change in enumerate(changes):
            change['year_week_str'] = relevant_weeks[index].as_param()
        return changes

    @cached_property
    def initial(self):
        """Return initial form values.

        Turn the decimals into integers already."""
        return {
            'hours_per_week': int(self.person.hours_per_week(
                year_week=self.chosen_year_week)),
            'standard_hourly_tariff': int(self.person.standard_hourly_tariff(
                year_week=self.chosen_year_week)),
            'minimum_hourly_tariff': int(self.person.minimum_hourly_tariff(
                year_week=self.chosen_year_week)),
            'target': int(self.person.target(
                year_week=self.chosen_year_week))}

    def form_valid(self, form):
        form.instance.person = self.person
        # We let the form machinery set the values, but they need to be
        # re-calculated for the initial values: they're used as culumative
        # values.
        hours_per_week = form.instance.hours_per_week or 0  # Adjust for None
        standard_hourly_tariff = form.instance.standard_hourly_tariff or 0
        minimum_hourly_tariff = form.instance.minimum_hourly_tariff or 0
        target = form.instance.target or 0  # Adjust for None
        form.instance.hours_per_week = (
            hours_per_week - self.initial['hours_per_week'])
        form.instance.standard_hourly_tariff = (
            standard_hourly_tariff - self.initial['standard_hourly_tariff'])
        form.instance.minimum_hourly_tariff = (
            minimum_hourly_tariff - self.initial['minimum_hourly_tariff'])
        form.instance.target = target - self.initial['target']
        form.instance.year_week = self.chosen_year_week

        adjusted = []
        if form.instance.hours_per_week:
            adjusted.append("werkweek")
        if form.instance.standard_hourly_tariff:
            adjusted.append("standaard uurtarief")
        if form.instance.minimum_hourly_tariff:
            adjusted.append("minimum uurtarief")
        if form.instance.target:
            adjusted.append("target")
        if adjusted:
            msg = ' en '.join(adjusted)
            msg = "%s aangepast" % msg.capitalize()
            msg += " (ingaande %s)" % self.chosen_year_week.formatted_first_day
            messages.success(self.request, msg)
        else:
            messages.info(self.request, "Niets aan te passen")
        return super(PersonChangeView, self).form_valid(form)


class OverviewsView(BaseView):
    template_name = 'trs/overviews.html'


class InvoicesView(BaseView):
    template_name = 'trs/invoices.html'
    normally_visible_filters = ['status', 'year']
    
    @cached_property
    def filters_and_choices(self):
        result = [
            {'title': 'Status',
             'param': 'status',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'alles',
                  'q': Q()},
                 {'value': 'false',
                  'title': 'nog niet betaald',
                  'q': Q(payed=None)}
             ]},
            {'title': 'Jaar',
             'param': 'year',
             'default': str(this_year_week().year),
             'choices': [
                 {'value': str(year),
                  'title': year,
                  'q': Q(date__year=year)}
                 for year in reversed(self.available_years)] + [
                         {'value': 'all',
                          'title': 'alle jaren',
                          'q': Q()}]},
            {'title': 'Maand',
             'param': 'month',
             'default': 'all',
             'choices': [
                 {'value': 'all',
                  'title': 'alles',
                  'q': Q()},
                 {'value': '1',
                  'title': 'jan',
                  'q': Q(date__month=1)},
                 {'value': '2',
                  'title': 'feb',
                  'q': Q(date__month=2)},
                 {'value': '3',
                  'title': 'mrt',
                  'q': Q(date__month=3)},
                 {'value': '4',
                  'title': 'apr',
                  'q': Q(date__month=4)},
                 {'value': '5',
                  'title': 'mei',
                  'q': Q(date__month=5)},
                 {'value': '6',
                  'title': 'jun',
                  'q': Q(date__month=6)},
                 {'value': '7',
                  'title': 'jul',
                  'q': Q(date__month=7)},
                 {'value': '8',
                  'title': 'aug',
                  'q': Q(date__month=8)},
                 {'value': '9',
                  'title': 'sep',
                  'q': Q(date__month=9)},
                 {'value': '10',
                  'title': 'okt',
                  'q': Q(date__month=10)},
                 {'value': '11',
                  'title': 'nov',
                  'q': Q(date__month=11)},
                 {'value': '12',
                  'title': 'dec',
                  'q': Q(date__month=12)},
             ]},
        ]

        return result

    def has_form_permissions(self):
        return self.can_see_everything

    @cached_property
    def year(self):
        return self.filters['year']

    @cached_property
    def available_years(self):
        this_year = this_year_week().year
        first_date = Invoice.objects.all().first().date
        first_year = first_date.year
        return list(range(first_year, this_year + 1))

    @cached_property
    def invoices(self):
        q_objects = [filter['q'] for filter in self.prepared_filters]
        result = Invoice.objects.filter(*q_objects)
        return result.select_related('project').order_by(
            '-date', '-number')

    @cached_property
    def total_exclusive(self):
        return sum([invoice.amount_exclusive or 0
                    for invoice in self.invoices])

    @cached_property
    def total_inclusive(self):
        return sum([invoice.amount_inclusive or 0
                    for invoice in self.invoices])


class InvoicesPerMonthOverview(BaseView):
    template_name = 'trs/invoices-per-month.html'

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
        invoices = Invoice.objects.all().values(
            'date', 'amount_exclusive')
        result = {year: {month: Decimal(0) for month in self.months}
                  for year in self.years}
        for invoice in invoices:
            year = invoice['date'].year
            month = invoice['date'].month
            if year not in self.years:
                continue
            result[year][month] += invoice['amount_exclusive']
        return result        

    @cached_property
    def rows(self):
        result = []
        base_url = (reverse('trs.overviews.invoices') +
                    '?year=%s&month=%s')
        for month in self.months:
            row = {'month': month,
                   'amounts': []}
            for year in self.years:
                value = self.years_and_months[year][month]
                url = base_url % (year, month)
                row['amounts'].append({'value': value,
                                       'url': url})
            result.append(row)
        return result
    

class ChangesOverview(BaseView):
    template_name = 'trs/changes.html'

    @cached_property
    def filters_and_choices(self):
        result = [
            {'title': 'Periode',
             'param': 'num_weeks',
             'default': '1',
             'choices': [
                 {'value': '1',
                  'title': 'alleen deze week',
                  'q': Q()},
                 {'value': '2',
                  'title': 'ook vorige week',
                  'q': Q()},
                 {'value': '4',
                  'title': 'volledige maand',
                  'q': Q()},
             ]},

            {'title': 'Projecten',
             'param': 'total',
             'default': 'true',
             'choices': [
                 {'value': 'true',
                  'title': 'alle projecten',
                  'q': Q()},
                 {'value': 'false',
                  'title': 'alleen de projecten waar je PL/PM voor bent',
                  'q': Q()},
             ]},
        ]
        return result

    @cached_property
    def num_weeks(self):
        """Return number of weeks to use for the summaries."""
        return self.filters['num_weeks']

    @cached_property
    def relevant_year_weeks(self):
        end = self.today
        start = self.today - datetime.timedelta(days=(self.num_weeks + 1) * 7)
        # ^^^ num_weeks + 1 to get a bit of padding halfway the week.
        return YearWeek.objects.filter(first_day__lte=end).filter(
            first_day__gte=start)

    @cached_property
    def start_week(self):
        return self.relevant_year_weeks[0]

    @cached_property
    def person_changes(self):
        changes = self.active_person.person_changes.filter(
            year_week__in=self.relevant_year_weeks).aggregate(
                models.Sum('hours_per_week'),
                models.Sum('target'),
                models.Sum('standard_hourly_tariff'),
                models.Sum('minimum_hourly_tariff'))
        changes = {k: v for k, v in changes.items() if v}
        return changes

    @cached_property
    def work_changes(self):
        result = []
        changes = self.active_person.work_assignments.filter(
            year_week__in=self.relevant_year_weeks,
            assigned_on__in=self.active_person.filtered_assigned_projects()
        ).values(
            'assigned_on').annotate(
                models.Sum('hours'),
                models.Sum('hourly_tariff'))
        changes = {change['assigned_on']:
                   {'hours': change['hours__sum'] or 0,
                    'hourly_tariff': change['hourly_tariff__sum'] or 0}
                   for change in changes}
        all_work_assignments = self.active_person.work_assignments.filter(
            assigned_on__in=self.active_person.filtered_assigned_projects()
        ).values(
            'assigned_on').annotate(
                models.Sum('hours'),
                models.Sum('hourly_tariff'))
        current_values = {
            work_assignment['assigned_on']:
            {'hours': work_assignment['hours__sum'] or 0,
             'hourly_tariff': work_assignment['hourly_tariff__sum'] or 0}
            for work_assignment in all_work_assignments}
        for project in self.active_person.filtered_assigned_projects():
            if project.id in changes:
                change = changes[project.id]
                change['project'] = project
                change['current'] = current_values[project.id]
                result.append(change)
        return result

    @cached_property
    def project_budget_changes(self):
        start = self.start_week.first_day
        is_project_leader = models.Q(
            project__project_leader=self.active_person)
        is_project_manager = models.Q(
            project__project_manager=self.active_person)
        added_after_start = models.Q(added__gte=start)
        budget_items = BudgetItem.objects.all()
        if not (self.can_see_everything and self.filters['total']):
            # Normally restrict it to relevant projects for you, but a manager
            # can see everything if desired.
            budget_items = budget_items.filter(
                is_project_manager | is_project_leader)
        budget_items = budget_items.filter(
            added_after_start).select_related(
                'project')
        projects = {budget_item.project.id: {
            'project': budget_item.project,
            'added': []} for budget_item in budget_items}
        for budget_item in budget_items:
            projects[budget_item.project.id]['added'].append(budget_item)
            # Hm, this can be done simpler, but now it matches the invoice
            # changes...
        return projects.values()

    @cached_property
    def project_invoice_changes(self):
        start = self.start_week.first_day
        is_project_leader = models.Q(
            project__project_leader=self.active_person)
        is_project_manager = models.Q(
            project__project_manager=self.active_person)
        added_after_start = models.Q(date__gte=start)
        payed_after_start = models.Q(date__gte=start)

        invoices = Invoice.objects.all()
        if not (self.can_see_everything and self.filters['total']):
            # Normally restrict it to relevant projects for you, but a manager
            # can see everything if desired.
            invoices = invoices.filter(
                is_project_manager | is_project_leader)
        invoices = invoices.filter(
            added_after_start | payed_after_start).select_related(
                'project')
        projects = {invoice.project.id: {'project': invoice.project,
                                         'added': [],
                                         'payed': []} for invoice in invoices}
        for invoice in invoices:
            if invoice.date >= start:
                projects[invoice.project.id]['added'].append(invoice)
            if invoice.payed is not None and invoice.payed >= start:
                projects[invoice.project.id]['payed'].append(invoice)
        return projects.values()

    @cached_property
    def are_there_changes(self):
        return (self.person_changes or self.work_changes or
                self.project_budget_changes or self.project_invoice_changes)

    @cached_property
    def vacation_left(self):
        """Return weeks and hours of vacation left."""
        vacation_projects = [project for project in self.active_projects
                             if project.description.lower() == 'verlof']
        if not vacation_projects:
            logger.warning("Couldn't find a project named 'verlof'")
            return
        vacation_project = vacation_projects[0]
        available = self.active_person.work_assignments.filter(
            assigned_on=vacation_project).aggregate(
                models.Sum('hours'))['hours__sum'] or 0
        used = self.active_person.bookings.filter(
            booked_on=vacation_project).aggregate(
                models.Sum('hours'))['hours__sum'] or 0
        hours_left = round(available - used)
        weeks_available = hours_left / (
            self.active_person.hours_per_week() or 40)
        return {'hours': hours_left,
                'weeks': weeks_available}


class ProjectLeadersAndManagersView(BaseView):
    template_name = 'trs/pl_pm.html'

    @cached_property
    def project_leaders(self):
        return Person.objects.filter(
            projects_i_lead__archived=False).distinct()

    @cached_property
    def project_managers(self):
        return Person.objects.filter(
            projects_i_manage__archived=False).distinct()


class CsvResponseMixin(object):

    prepend_lines = []
    header_line = []
    csv_lines = []

    def title_to_filename(self):
        name = self.title.lower()
        if getattr(self, 'small_title', None):
            name = name + ' ' + self.small_title.lower()
        # Brute force
        name = [char for char in name
                if char in 'abcdefghijklmnopqrstuvwxyz-_ 0123456789']
        name = ''.join(name)
        name = name.replace(' ', '_')
        return name

    @property
    def csv_filename(self):
        return self.title_to_filename()

    def render_to_response(self, context, **response_kwargs):
        """Return a csv response instead of a rendered template."""
        response = HttpResponse(mimetype='text/csv')
        filename = self.csv_filename + '.csv'
        response[
            'Content-Disposition'] = 'attachment; filename="%s"' % filename

        # Ideally, use something like .encode('cp1251') somehow somewhere.
        writer = csv.writer(response, delimiter=";")

        for line in self.prepend_lines:
            writer.writerow(line)
        writer.writerow(self.header_line)
        for line in self.csv_lines:
            # Note: line should be a list of values.
            writer.writerow(line)
        return response


class ProjectsCsvView(CsvResponseMixin, ProjectsView):

    def has_form_permissions(self):
        return self.can_view_elaborate_version

    header_line = [
        'Code',
        'Omschrijving',
        'Opdrachtgever',
        'Groep',
        'Intern',
        'Gesubsidieerd',
        'Gearchiveerd',
        'Start',
        'Einde',
        'PL',
        'PM',
        'Opdrachtsom',
        'Startoverleg',
        'Geaccepteerd',

        'Gefactureerd',
        'Omzet',
        'Personele kosten incl reservering',
        'Overige kosten',
        'Gefactureerd t.o.v. opdrachtsom',
        'Gefactureerd t.o.v. omzet + extra kosten',

        'Opmerking',
        'Financiele opmerking',
    ]

    @property
    def csv_lines(self):
        for line in self.lines:
            project = line['project']
            remark = ''
            financial_remark = ''
            if project.remark:
                remark = '   '.join(project.remark.splitlines())
            if project.financial_remark:
                financial_remark = '   '.join(
                    project.financial_remark.splitlines())
            result = [
                project.code,
                project.description,
                project.principal,
                project.group,
                project.internal,
                project.is_subsidized,
                project.archived,
                project.start.first_day,
                project.end.first_day,
                project.project_leader,
                project.project_manager,
                project.contract_amount,
                project.startup_meeting_done,
                project.is_accepted,

                line['invoice_amount'],
                line['turnover'],
                line['person_costs_incl_reservation'],
                line['other_costs'],
                line['invoice_amount_percentage'],
                line['invoice_versus_turnover_percentage'],

                remark,
                financial_remark,
            ]
            yield(result)


class PersonsCsvView(CsvResponseMixin, PersonsView):

    def has_form_permissions(self):
        return self.can_view_elaborate_version

    header_line = [
        'Naam',
        'Nog te boeken',
        'Buiten budget geboekt',
        'Binnen budget percentage',
        'Extern percentage',
        'Intern percentage',
        'Target percentage',
        'Target',
        'Omzet',
        'Werkvoorraad',
        'Werkvoorraad als omzet',
        ]

    @property
    def csv_lines(self):
        for line in self.lines:
            person = line['person']
            pyc = line['pyc']
            result = [
                person.name,
                person.to_book()['hours'],
                pyc.overbooked,
                pyc.well_booked_percentage,
                pyc.billable_percentage,
                pyc.unbillable_percentage,
                pyc.target_percentage,
                person.target(),
                pyc.turnover,
                pyc.left_to_book_external,
                pyc.left_to_turn_over,
                ]
            yield result


class ProjectCsvView(CsvResponseMixin, ProjectView):

    def has_form_permissions(self):
        return self.can_see_project_financials

    @cached_property
    def weeks(self):
        return YearWeek.objects.filter(
            first_day__gte=self.project.start.first_day,
            first_day__lte=self.project.end.first_day)

    @cached_property
    def bookings_per_week_per_person(self):
        bookings = Booking.objects.filter(
            booked_on=self.project,
            year_week__in=self.weeks).values(
                'booked_by',
                'year_week').annotate(
                    models.Sum('hours'))
        return {(booking['booked_by'], booking['year_week']):
                round(booking['hours__sum'])
                for booking in bookings}

    @property
    def prepend_lines(self):
        return [['Code', self.project.code],
                ['Naam', self.project.description],
                ['Opdrachtgever', self.project.principal],
                [],
                []]

    @property
    def header_line(self):
        result = [
            'Naam',
            'Uren achter met boeken',
            'PM/PL',
            'Toegekende uren',
            'Tarief',
            'Kosten',
            'Inkomsten',
            'Geboekt',
            'Omzet',
            'Verlies',
            ''
        ]
        result += [week.as_param() for week in self.weeks]
        return result

    @property
    def csv_lines(self):
        for line in self.lines:
            person = line['person']
            pl = (person == self.project.project_leader) and 'PL' or ''
            pm = (person == self.project.project_manager) and 'PM' or ''
            result = [
                person.name,
                person.to_book()['hours'],
                ' '.join([pl, pm]),
                line['budget'],
                line['hourly_tariff'],
                line['planned_turnover'],
                '',
                line['booked'],
                line['turnover'],
                line['loss'],
                '',
            ]
            result += [
                self.bookings_per_week_per_person.get((person.pk, week.pk), 0)
                for week in self.weeks]

            yield result

        yield(['Reservering',
               '',
               '',
               '',
               '',
               self.project.reservation,
           ])

        yield(['Subtotaal',
               '',
               '',
               '',
               '',
               self.person_costs_incl_reservation,
               '',
               '',
               self.total_turnover,
               self.total_loss,
           ])
        yield([])

        for budget_item in self.project.budget_items.all():
            yield([
                budget_item.description,
                '',
                '',
                '',
                '',
                (budget_item.amount > 0) and budget_item.amount or '',
                (budget_item.amount <= 0) and budget_item.amount_as_income() or '',
            ])

        yield(['Opdrachtsom',
               '',
               '',
               '',
               '',
               '',
               self.project.contract_amount,
           ])
        yield(['Totaal',
               '',
               '',
               '',
               '',
               self.total_costs,
               self.total_income,
           ])

        yield(['Nog te verdelen',
               '',
               '',
               '',
               '',
               '',
               self.project.left_to_dish_out(),
           ])


class ReservationsOverview(BaseView):
    template_name = 'trs/reservations.html'

    filters_and_choices = [
        {'title': 'Filter',
         'param': 'filter',
         'default': 'active',
         'choices': [
             {'value': 'active',
              'title': 'huidige projecten',
              'q': Q(archived=False)},
             {'value': 'all',
              'title': 'alle projecten (inclusief archief)',
              'q': Q()},
         ]},
    ]

    def has_form_permissions(self):
        return self.can_see_everything

    @cached_property
    def projects(self):
        q_objects = [filter['q'] for filter in self.prepared_filters]
        return Project.objects.filter(*q_objects).filter(
            reservation__gt=0)
