import datetime
import logging
import time

from django import forms
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import models
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


class BaseMixin(object):
    template_name = 'trs/base.html'
    title = "TRS tijdregistratiesysteem"

    @cached_property
    def today(self):
        return datetime.date.today()

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
        return core.get_pyc(person=self.sidebar_person)

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
            if not 'admin_override_active' in self.request.session:
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


class BaseView(LoginAndPermissionsRequiredMixin, TemplateView, BaseMixin):
    pass


class HomeView(BaseView):
    template_name = 'trs/home.html'

    @cached_property
    def num_weeks(self):
        """Return number of weeks to use for the summaries."""
        # Optionally add GET query param for this. Default is 2 now.
        return 2

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
        for project in self.active_person.filtered_assigned_projects():
            changes = self.active_person.work_assignments.filter(
                year_week__in=self.relevant_year_weeks,
                assigned_on=project).aggregate(
                    models.Sum('hours'),
                    models.Sum('hourly_tariff'))
            changes = {k: v for k, v in changes.items() if v}
            if changes:
                changes['project'] = project  # Inject for template.
                result.append(changes)
        return result

    # TODO: project_budget_item_changes
    @cached_property
    def project_invoice_changes(self):
        result = []
        for project in (list(self.active_person.projects_i_lead.all()) +
                        list(self.active_person.projects_i_manage.all())):
            start = self.start_week.first_day
            added = project.invoices.filter(added__gt=start)
            payed = project.invoices.filter(payed__gt=start)
            if added or payed:
                change = {'project': project,
                          'added': added,
                          'payed': payed}
                result.append(change)
        return result

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
        weeks_available = hours_left / self.active_person.hours_per_week()
        return {'hours': hours_left,
                'weeks': weeks_available}


class PersonsView(BaseView):
    @property
    def template_name(self):
        if self.can_view_elaborate_version:
            return 'trs/persons.html'
        return 'trs/persons-simple.html'

    @cached_property
    def can_view_elaborate_version(self):
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def can_add_person(self):
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def persons(self):
        return Person.objects.filter(archived=False)

    @cached_property
    def lines(self):
        # This is the elaborate view for management.
        return [{'person': person, 'pyc': core.get_pyc(person)}
                for person in self.persons]


class PersonView(BaseView):
    template_name = 'trs/person.html'

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
        return self.person.filtered_assigned_projects()

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
            item['assigned_on']: round(item['hours__sum'])
            for item in budget_per_project}
        hourly_tariffs = {
            item['assigned_on']: round(item['hourly_tariff__sum'])
            for item in budget_per_project}
        # Hours worked query.
        booked_per_project = Booking.objects.filter(
            booked_by=self.person,
            booked_on__in=self.projects).values(
                'booked_on').annotate(
                    models.Sum('hours'))
        booked = {item['booked_on']: round(item['hours__sum'])
                  for item in booked_per_project}

        for project in self.projects:
            line = {'project': project}
            line['budget'] = budgets.get(project.id, 0)
            line['booked'] = booked.get(project.id, 0)
            line['is_overbooked'] = line['booked'] > line['budget']
            line['left_to_book'] = max(0, line['budget'] - line['booked'])
            line['is_project_leader'] = (
                project.project_leader_id == self.person.id)
            line['is_project_manager'] = (
                project.project_manager_id == self.person.id)
            line['hourly_tariff'] = hourly_tariffs.get(project.id, 0)
            line['turnover'] = (
                min(line['budget'], line['booked']) * line['hourly_tariff'])
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


class BookingOverview(PersonView):
    template_name = 'trs/booking_overview.html'
    # xxx

    @cached_property
    def year(self):
        # TODO: GET param for year.
        return this_year_week().year

    @cached_property
    def lines(self):
        booked_this_year_per_week = Booking.objects.filter(
            booked_by=self.person,
            year_week__year=self.year).values(
                'year_week__week').annotate(
                    models.Sum('hours'))
        booked_per_week = {
            item['year_week__week']: round(item['hours__sum'])
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
            booked = booked_per_week.get(year_week.week, 0)
            klass = ''
            hint = ''
            if booked < to_book:
                klass = 'danger'
                hint = "Te boeken: %s" % round(to_book)
            result.append({'year_week': year_week,
                           'to_book': to_book,
                           'booked': booked,
                           'klass': klass,
                           'hint': hint})
        return result


class ProjectsView(BaseView):

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
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def projects(self):
        all_projects = Project.objects.filter(archived=False)
        if self.can_view_elaborate_version:
            return all_projects
        return all_projects.filter(hidden=False)

    @cached_property
    def lines(self):
        # Used for the elaborate view (projects.html)
        result = []
        invoices_per_project = Invoice.objects.filter(
            project__in=self.projects).values(
            'project').annotate(
            models.Sum('amount_exclusive'))
        invoice_amounts = {item['project']: round(item['amount_exclusive__sum'])
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
            if project.contract_amount:
                invoice_amount_percentage = round(
                    invoice_amount / project.contract_amount * 100)
            else:  # Division by zero.
                invoice_amount_percentage = None
            if turnover + costs:
                invoice_versus_turnover_percentage = round(
                    invoice_amount / (turnover + costs) * 100)
            else:
                invoice_versus_turnover_percentage = None
            line['contract_amount'] = project.contract_amount
            line['invoice_amount'] = invoice_amount
            line['turnover'] = turnover
            line['costs'] = costs
            line['invoice_amount_percentage'] = invoice_amount_percentage
            line['invoice_versus_turnover_percentage'] = (
                invoice_versus_turnover_percentage)
            result.append(line)
        return result

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
    def can_view_team(self):
        if not self.project.hidden:
            # Normally everyone can see it.
            return True
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True
        if self.project.project_manager == self.active_person:
            return True

    @cached_property
    def can_edit_project(self):
        # True even when the project is archived: you must be able to un-set
        # the archive bit. To compensate for this, the title of the edit page
        # has a big fat "you're editing an archived project!" warning.
        if self.can_edit_and_see_everything:
            return True

    @cached_property
    def can_edit_financials(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_manager == self.active_person:
            return True

    @cached_property
    def can_edit_team(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            # Whatever happens, a PL can still add persons to the project for
            # zero hours and a zero tariff.
            return True
        if self.project.is_accepted:
            # Not editable anymore for project managers and others.
            return False

    @cached_property
    def can_see_financials(self):
        if self.can_edit_and_see_everything:
            return True
        if self.active_person in self.project.assigned_persons():
            return True
        if self.project.project_leader == self.active_person:
            return True
        if self.project.project_manager == self.active_person:
            return True

    @cached_property
    def can_see_project_financials(self):
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True
        if self.project.project_manager == self.active_person:
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
            item['assigned_to']: round(item['hours__sum'])
            for item in budget_per_person}
        hourly_tariffs = {
            item['assigned_to']: round(item['hourly_tariff__sum'])
            for item in budget_per_person}
        # Hours worked query.
        booked_per_person = Booking.objects.filter(
            booked_by__in=self.persons,
            booked_on=self.project).values(
                'booked_by').annotate(
                    models.Sum('hours'))
        booked = {item['booked_by']: round(item['hours__sum'])
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
            line['turnover'] = (
                min(line['budget'], line['booked']) * line['hourly_tariff'])
            line['loss'] = (
                max(0, (line['booked'] - line['budget'])) * line['hourly_tariff'])
            line['left_to_turn_over'] = line['left_to_book'] * line['hourly_tariff']
            line['desired_hourly_tariff'] = round(person.standard_hourly_tariff(
                year_week=self.project.start))
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
    def person_costs(self):
        return -1 * self.total_turnover

    @cached_property
    def total(self):
        budget = self.project.budget_items.all().aggregate(
            models.Sum('amount'))['amount__sum'] or 0
        return self.project.contract_amount + budget + self.person_costs

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
        """Per definition, return True.

        No permission checks needed. What you get and what you edit are the
        active_person's hours. And you are yourself! This might change later
        on when office management gets the option to change someone's hours.
        """
        return True

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
            work_assignments__assigned_to=self.active_person,
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
        """Return initial form values. Turn the decimals into integers already."""
        result = {}
        bookings = Booking.objects.filter(
            year_week=self.active_year_week,
            booked_by=self.active_person,
            booked_on__in=self.relevant_projects).values(
                'booked_on__code').annotate(
                    models.Sum('hours'))
        result = {item['booked_on__code']: round(item['hours__sum'])
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
                                  booked_by=self.active_person,
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
        return self.active_year_week.get_absolute_url()

    @cached_property
    def lines(self):
        """Return project plus a set of four hours."""
        result = []
        form = self.get_form(self.get_form_class())
        fields = list(form)  # A form's __iter__ returns 'bound fields'.
        # Prepare booking info as one query.
        booking_table = Booking.objects.filter(
            year_week__in=self.year_weeks_to_display,
            booked_by=self.active_person).values(
                'booked_on', 'year_week').annotate(
                    models.Sum('hours'))
        bookings = {(item['booked_on'], item['year_week']): item['hours__sum']
                    for item in booking_table}
        # Idem for budget
        budget_per_project = WorkAssignment.objects.filter(
            assigned_to=self.active_person,
            assigned_on__in=self.relevant_projects).values(
                'assigned_on').annotate(
                    models.Sum('hours'))
        budgets = {item['assigned_on']: round(item['hours__sum'])
                   for item in budget_per_project}
        # Item for hours worked.
        booked_per_project = Booking.objects.filter(
            booked_by=self.active_person,
            booked_on__in=self.relevant_projects).values(
                'booked_on').annotate(
                    models.Sum('hours'))
        booked_total = {item['booked_on']: round(item['hours__sum'])
                        for item in booked_per_project}

        this_year = this_year_week().year
        for project_index, project in enumerate(self.relevant_projects):
            line = {'project': project}
            for index, year_week in enumerate(self.year_weeks_to_display):
                booked = bookings.get((project.id, year_week.id), 0)
                key = 'hours%s' % index
                line[key] = booked

            # Filtering if we're allowed to book or not.
            if not (project.archived or
                    # TODO: figure out proper python3 comparisons... Shame on me.
                    str(project.start) > str(self.active_year_week) or
                    str(project.end) < str(self.active_year_week) or
                    self.active_year_week.year < this_year):
                line['field'] = fields[project_index]
            else:
                line['field'] = round(bookings.get(
                    (project.id, self.active_year_week.id), 0))

            line['budget'] = budgets.get(project.id, 0)
            line['booked_total'] = booked_total.get(project.id, 0)
            line['is_overbooked'] = line['booked_total'] > line['budget']
            line['left_to_book'] = max(0, line['budget'] - line['booked_total'])
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
    fields = ['code', 'description', 'internal', 'hidden', 'hourless',
              'archived',  # Note: archived only on edit view :-)
              'is_subsidized', 'principal',
              'contract_amount',
              'start', 'end', 'project_leader', 'project_manager',
              'is_accepted',  # Note: is_accepted only on edit view!
              'remark',
    ]

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
        # Editable even when archived as you must be able to un-set the
        # 'archive' bit. If archived, the title warns you in no uncertain way.
        if self.can_edit_and_see_everything:
            return True

    def form_valid(self, form):
        messages.success(self.request, "Project aangepast")
        return super(ProjectEditView, self).form_valid(form)


class ProjectCreateView(LoginAndPermissionsRequiredMixin,
                        CreateView,
                        BaseMixin):
    template_name = 'trs/edit.html'
    model = Project
    title = "Nieuw project"
    fields = ['code', 'description', 'internal', 'hidden', 'hourless',
              'is_subsidized', 'principal',
              'contract_amount',
              'start', 'end', 'project_leader', 'project_manager',
              'remark',
    ]

    def has_form_permissions(self):
        if self.can_edit_and_see_everything:
            return True

    def form_valid(self, form):
        messages.success(self.request, "Project aangemaakt")
        return super(ProjectCreateView, self).form_valid(form)


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
    template_name = 'trs/edit.html'
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
    def success_url(self):
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
    fields = ['description', 'amount', 'is_reservation']

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
        messages.success(self.request, "Begrotingsitem toegevoegd")
        return super(BudgetItemCreateView, self).form_valid(form)


class BudgetItemEditView(LoginAndPermissionsRequiredMixin,
                         UpdateView,
                         BaseMixin):
    template_name = 'trs/edit.html'
    model = BudgetItem
    fields = ['description', 'amount', 'is_reservation']

    @property
    def title(self):
        return "Aanpassen begrotingsitem voor %s" % self.project.code

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
        messages.success(self.request, "Begrotingsitem aangepast")
        return super(BudgetItemEditView, self).form_valid(form)


class PersonEditView(LoginAndPermissionsRequiredMixin,
                     UpdateView,
                     BaseMixin):
    template_name = 'trs/edit.html'
    model = Person
    fields = ['name', 'user', 'is_management', 'archived']

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
    fields = ['name', 'user', 'is_management']

    def has_form_permissions(self):
        if self.can_edit_and_see_everything:
            return True

    def form_valid(self, form):
        messages.success(self.request, "Medewerker aangemaakt")
        return super(PersonCreateView, self).form_valid(form)


class TeamEditView(LoginAndPermissionsRequiredMixin, FormView, BaseMixin):
    template_name = 'trs/team.html'

    def has_form_permissions(self):
        if self.project.archived:
            return False
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True
        if self.project.project_manager == self.active_person:
            return True

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['pk'])

    @cached_property
    def title(self):
        return "Projectteam voor %s bewerken" % self.project.code

    @cached_property
    def can_edit_hours(self):
        # TODO: add docstring with meaning.
        if self.can_edit_and_see_everything:
            return True
        if self.project.is_accepted:
            return False
        if self.project.project_leader == self.active_person:
            return True

    @cached_property
    def can_add_team_member(self):
        if self.can_edit_and_see_everything:
            return True
        if self.project.project_leader == self.active_person:
            return True  # Even if is_accepted is True, btw!

    @cached_property
    def can_edit_hourly_tariff(self):
        if self.can_edit_and_see_everything:
            return True
        if self.project.is_accepted:
            return False
        if self.project.project_manager == self.active_person:
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
        booked = {item['booked_by']: round(item['hours__sum'])
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
            result.append(line)
        return result

    @cached_property
    def new_team_member_field(self):
        if self.can_add_team_member:
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
            messages.success(self.request, "Teamleden: %s gewijzigd" % num_changes)

        if self.can_add_team_member:
            new_team_member_id = form.cleaned_data.get('new_team_member')
            if new_team_member_id:
                person = Person.objects.get(id=new_team_member_id)
                msg = "%s is aan het team toegevoegd" % person.name
                hourly_tariff = person.standard_hourly_tariff()
                if self.project.is_accepted:
                    # Oops, we cannot change the financials of the project,
                    # but as project leader we *are* always allowed to add
                    # someone to the project. But... the hourly tariff is zero
                    # in that case.
                    hourly_tariff = 0
                    msg += " (opgepast: voor nultarief)"
                work_assignment = WorkAssignment(
                    assigned_on=self.project,
                    assigned_to=person,
                    hourly_tariff=hourly_tariff)
                work_assignment.save()
                logger.info(msg)
                messages.success(self.request, msg)

        return super(TeamEditView, self).form_valid(form)

    @cached_property
    def success_url(self):
        return reverse('trs.project.team', kwargs={'pk': self.project.pk})

    @cached_property
    def back_url(self):
        template = '<div><small><a href="{url}">&larr; {text}</a></small></div>'
        url = self.project.get_absolute_url()
        text = "Terug naar het project"
        return mark_safe(template.format(url=url, text=text))


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
        return '.?year_week=%s' % self.chosen_year_week

    @cached_property
    def chosen_year_week(self):
        if not 'year_week' in self.request.GET:
            return this_year_week()
        year, week = self.request.GET['year_week'].split('-')
        return YearWeek.objects.get(year=int(year), week=int(week))

    def year_week_suggestions(self):
        current_year = this_year_week().year
        next_year = current_year + 1
        return [
            # (yyyy-ww, title)
            (str(YearWeek.objects.filter(year=current_year).first()),
             'Begin %s (begin dit jaar)' % current_year),
            (str(this_year_week()),
             'Nu'),
            (str(YearWeek.objects.filter(year=next_year).first()),
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
            change['year_week_str'] = str(relevant_weeks[index])
        return changes

    @cached_property
    def initial(self):
        """Return initial form values. Turn the decimals into integers already."""
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
            messages.success(self.request, msg)
        else:
            messages.info(self.request, "Niets aan te passen")
        return super(PersonChangeView, self).form_valid(form)


class OverviewsView(BaseView):
    template_name = 'trs/overviews.html'


class InvoicesView(BaseView):
    template_name = 'trs/invoices.html'

    def has_form_permissions(self):
        return self.can_edit_and_see_everything

    @cached_property
    def invoices(self):
        return Invoice.objects.all().prefetch_related('project').order_by(
            '-date')
