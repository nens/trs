import datetime
import logging

from django import forms
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.db import models
from django.shortcuts import redirect
from django.utils.datastructures import SortedDict
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView

from trs import core
from trs.models import Person
from trs.models import Project
from trs.models import Booking
from trs.models import YearWeek
from trs.models import WorkAssignment
from trs.models import BudgetAssignment
from trs.models import this_year_week
from trs.templatetags.trs_formatting import hours as format_as_hours
from trs.templatetags.trs_formatting import money as format_as_money


logger = logging.getLogger()


class LoginRequiredMixin(object):
    """See http://stackoverflow.com/a/10304880/27401"""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


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
        if persons:
            person = persons[0]
            logger.debug("Found active person: %s", person)
            return person

    @cached_property
    def active_projects(self):
        # TODO: extra filtering for projects that are past their date.
        if not self.active_person:
            return []
        return self.active_person.assigned_projects()

    @cached_property
    def person_year_info(self):
        if not self.active_person:
            return
        return core.PersonYearCombination(person=self.active_person)


class BaseView(LoginRequiredMixin, TemplateView, BaseMixin):
    pass


class HomeView(BaseView):
    template_name = 'trs/home.html'


class PersonsView(BaseView):
    template_name = 'trs/persons.html'

    @cached_property
    def persons(self):
        return Person.objects.all()


class PersonView(BaseView):
    template_name = 'trs/person.html'

    @cached_property
    def person(self):
        return Person.objects.get(pk=self.kwargs['pk'])

    @cached_property
    def person_projects(self):
        return [core.ProjectPersonCombination(project, self.person)
                for project in self.person.assigned_projects()]

    @cached_property
    def total_budget(self):
        return sum([project.budget for project in self.person_projects])

    @cached_property
    def total_booked(self):
        return sum([project.booked for project in self.person_projects])

    @cached_property
    def total_left_to_book(self):
        return sum([project.left_to_book for project in self.person_projects])


class ProjectsView(BaseView):
    template_name = 'trs/projects.html'

    @cached_property
    def projects(self):
        return Project.objects.all()


class ProjectView(BaseView):
    template_name = 'trs/project.html'

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['pk'])

    @cached_property
    def person_projects(self):
        return [core.ProjectPersonCombination(self.project, person)
                for person in self.project.assigned_persons()]

    @cached_property
    def total_turnover(self):
        return sum([person_project.turnover
                    for person_project in self.person_projects])

    @cached_property
    def total_turnover_left(self):
        return sum([person_project.left_to_turn_over
                    for person_project in self.person_projects])

    @cached_property
    def subtotal(self):
        return self.project.budget_assignments.all().aggregate(
            models.Sum('budget'))['budget__sum'] or 0

    @cached_property
    def amount_left(self):
        return self.subtotal - self.total_turnover - self.total_turnover_left


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


class BookingView(LoginRequiredMixin, FormView, BaseMixin):
    # TODO: also allow /booking/yyyy-ww/ format.
    template_name = 'trs/booking.html'

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
        return YearWeek.objects.filter(first_day__lte=end).filter(
            first_day__gte=start)

    def get_form_class(self):
        """Return dynamically generated form class."""
        fields = SortedDict()
        for index, project in enumerate(self.active_projects):
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
        for project in self.active_projects:
            booked = Booking.objects.filter(
                year_week=self.active_year_week,
                booked_by=self.active_person,
                booked_on=project).aggregate(
                    models.Sum('hours'))['hours__sum'] or 0
            result[project.code] = int(booked)
        return result

    def form_valid(self, form):
        total_difference = 0
        absolute_difference = 0
        for project_code, new_hours in form.cleaned_data.items():
            old_hours = self.initial[project_code]
            difference = new_hours - old_hours
            total_difference += difference
            absolute_difference += abs(difference)
            if difference:
                project = [project for project in self.active_projects
                           if project.code == project_code][0]
                booking = Booking(hours=difference,
                                  booked_by=self.active_person,
                                  booked_on=project,
                                  year_week=self.active_year_week)
                booking.save()
                logger.info("Added booking %s", booking)
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

        return super(BookingView, self).form_valid(form)

    @cached_property
    def tabindex_submit_button(self):
        return len(self.active_projects) + 1

    @cached_property
    def success_url(self):
        return self.active_year_week.get_absolute_url()

    @cached_property
    def lines(self):
        """Return project plus a set of four hours."""
        result = []
        form = self.get_form(self.get_form_class())
        fields = list(form)  # A form's __iter__ returns 'bound fields'.
        for project_index, project in enumerate(self.active_projects):
            line = {'ppc': core.ProjectPersonCombination(project,
                                                         self.active_person)}
            for index, year_week in enumerate(self.year_weeks_to_display):
                booked = Booking.objects.filter(
                    year_week=year_week,
                    booked_by=self.active_person,
                    booked_on=project).aggregate(
                        models.Sum('hours'))['hours__sum'] or 0
                key = 'hours%s' % index
                line[key] = booked
            line['field'] = fields[project_index]
            result.append(line)
        return result


class ProjectEditView(UpdateView, BaseMixin):
    template_name = 'trs/edit.html'
    model = Project
    title = "Project aanpassen"

    def form_valid(self, form):
        messages.success(self.request, "Project aangepast")
        return super(ProjectEditView, self).form_valid(form)


class ProjectCreateView(CreateView, BaseMixin):
    template_name = 'trs/edit.html'
    model = Project
    title = "Nieuw project"

    def form_valid(self, form):
        messages.success(self.request, "Project aangemaakt")
        return super(ProjectCreateView, self).form_valid(form)


class TeamEditView(LoginRequiredMixin, FormView, BaseMixin):
    template_name = 'trs/team.html'

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['pk'])

    @cached_property
    def ppc(self):
        return core.ProjectPersonCombination(self.project, self.active_person)

    @cached_property
    def title(self):
        return "Projectteam voor %s bewerken" % self.project.code

    @cached_property
    def can_edit_hours(self):
        # TODO: can_edit_role (also PL territory)
        #return self.ppc.is_project_leader
        return True

    @cached_property
    def can_add_team_member(self):
        #return self.ppc.is_project_leader
        return True

    @cached_property
    def can_edit_hourly_tariff(self):
        #return self.ppc.is_project_manager
        return True

    def hours_fieldname(self, person):
        return 'hours-%s' % person.id

    def hourly_tariff_fieldname(self, person):
        return 'hourly_tariff-%s' % person.id

    def get_form_class(self):
        """Return dynamically generated form class."""
        fields = SortedDict()
        tabindex = 1
        for index, person in enumerate(self.project.assigned_persons()):
            ppc = core.ProjectPersonCombination(self.project, person)
            if self.can_edit_hours:
                field_type = forms.IntegerField(
                    min_value=0,
                    initial=round(ppc.budget),
                    widget=forms.TextInput(attrs={'size': 4,
                                                  'tabindex': tabindex}))
                fields[self.hours_fieldname(person)] = field_type
                tabindex += 1
            if self.can_edit_hourly_tariff:
                field_type = forms.IntegerField(
                    min_value=0,
                    initial=round(ppc.hourly_tariff),
                    widget=forms.TextInput(attrs={'size': 4,
                                                  'tabindex': tabindex}))
                fields[self.hourly_tariff_fieldname(person)] = field_type
                tabindex += 1
        if self.can_add_team_member:
            # New team member field
            name = 'new_team_member'
            choices = list(Person.objects.all().values_list('pk', 'name'))
            choices.insert(0, ('', '---'))
            # TODO: ^^^ filter out inactive users.
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
        for person in self.project.assigned_persons():
            ppc = core.ProjectPersonCombination(self.project, person)
            line = {'ppc': ppc}
            if self.can_edit_hours:
                line['hours'] = fields[field_index]
                field_index += 1
            else:
                line['hours'] = format_as_hours(ppc.budget)
            if self.can_edit_hourly_tariff:
                line['hourly_tariff'] = fields[field_index]
                field_index += 1
            else:
                line['hourly_tariff'] = format_as_money(ppc.hourly_tariff)
            result.append(line)
        return result

    @cached_property
    def new_team_member_field(self):
        if self.can_add_team_member:
            return self.bound_form_fields[-1]

    def form_valid(self, form):
        num_changes = 0
        for person in self.project.assigned_persons():
            ppc = core.ProjectPersonCombination(self.project, person)
            hours = 0
            hourly_tariff = 0
            if self.can_edit_hours:
                current = ppc.budget
                new = form.cleaned_data.get(self.hours_fieldname(person))
                hours = new - current
            if self.can_edit_hourly_tariff:
                current = ppc.hourly_tariff
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
                work_assignment = WorkAssignment(
                    assigned_on=self.project,
                    assigned_to=person)
                work_assignment.save()
                msg = "Added %s to team" % person.name
                logger.info(msg)
                messages.success(self.request, msg)

        return super(TeamEditView, self).form_valid(form)

    @cached_property
    def success_url(self):
        return self.project.get_absolute_url()


class BudgetAddView(CreateView, BaseMixin):
    template_name = 'trs/edit.html'
    model = BudgetAssignment
    fields = ['budget', 'description']
    hidden_fields = ['assigned_to']

    @property
    def title(self):
        return "Nieuwe budgetaanpassing voor %s" % self.project.code

    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs['pk'])

    @cached_property
    def success_url(self):
        return self.project.get_absolute_url()

    def form_valid(self, form):
        form.instance.assigned_to = self.project
        messages.success(self.request, "Budget aangepast")
        return super(BudgetAddView, self).form_valid(form)
