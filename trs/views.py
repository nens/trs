import datetime
import logging

from django import forms
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
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import CreateView

from trs import core
from trs.models import Person
from trs.models import Project
from trs.models import Booking
from trs.models import YearWeek
from trs.models import WorkAssignment
from trs.models import this_year_week


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
        for project_code, new_hours in form.cleaned_data.items():
            old_hours = self.initial[project_code]
            difference = new_hours - old_hours
            if difference:
                project = [project for project in self.active_projects
                           if project.code == project_code][0]
                booking = Booking(hours=difference,
                                  booked_by=self.active_person,
                                  booked_on=project,
                                  year_week=self.active_year_week)
                booking.save()
                logger.info("Added booking %s", booking)
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
            line = {'project': project}
            # import pdb;pdb.set_trace()
            line['available'] = WorkAssignment.objects.filter(
                assigned_to=self.active_person,
                assigned_on=project).aggregate(
                    models.Sum('hours'))['hours__sum']
            line['already_booked'] = Booking.objects.filter(
                    booked_by=self.active_person,
                    booked_on=project).aggregate(
                        models.Sum('hours'))['hours__sum']
            line['overbooked'] = (line['already_booked'] > line['available'])
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


class ProjectCreateView(CreateView, BaseMixin):
    template_name = 'trs/edit.html'
    model = Project
    title = "Nieuw project"
