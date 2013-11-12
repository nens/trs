import datetime
import logging

from django import forms
from django.db import models
from django.utils.datastructures import SortedDict
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from trs.models import Person
from trs.models import Project
from trs.models import Booking
from trs.models import YearWeek
from trs.models import WorkAssignment


logger = logging.getLogger()


class BaseMixin(object):
    template_name = 'trs/base.html'
    title = "TRS tijdregistratiesysteem"

    @property
    def today(self):
        return datetime.date.today()

    @property
    def active_person(self):
        if self.request.user.is_anonymous():
            logger.debug("Anonymous user")
            return
        persons = Person.objects.filter(user=self.request.user)
        if persons:
            person = persons[0]
            logger.debug("Found active person: {}", person)
            return person

    @property
    def active_projects(self):
        # TODO: extra filtering for projects that are past their date.
        if not self.active_person:
            return []
        return self.active_person.assigned_projects()


class BaseView(TemplateView, BaseMixin):
    pass

class HomeView(BaseView):
    template_name = 'trs/home.html'


class PersonsView(BaseView):
    template_name = 'trs/persons.html'

    @property
    def persons(self):
        return Person.objects.all()


class PersonView(BaseView):
    template_name = 'trs/person.html'

    @property
    def person(self):
        return Person.objects.get(slug=self.kwargs['slug'])


class ProjectsView(BaseView):
    template_name = 'trs/projects.html'

    @property
    def projects(self):
        return Project.objects.all()


class ProjectView(BaseView):
    template_name = 'trs/project.html'

    @property
    def project(self):
        return Project.objects.get(slug=self.kwargs['slug'])


class BookingView(FormView, BaseMixin):
    # TODO: also allow /booking/yyyy-ww/ format.
    template_name = 'trs/booking.html'

    @property
    def active_year_week(self):
        year = self.kwargs.get('year')
        week = self.kwargs.get('week')
        if year is not None:  # (Week is also not None, then)
            return YearWeek.objects.get(year=year, week=week)
        # Default: this week's first day.
        this_year_week = YearWeek.objects.filter(
            first_day__lte=self.today).last()
        return this_year_week

    @property
    def active_first_day(self):
        return self.active_year_week.first_day

    @property
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

    @property
    def initial(self):
        result = {}
        for project in self.active_projects:
            booked = Booking.objects.filter(
                year_week=self.active_year_week,
                booked_by=self.active_person,
                booked_on=project).aggregate(
                    models.Sum('hours'))['hours__sum']
            if booked is None:
                booked = 0
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

    @property
    def tabindex_submit_button(self):
        return len(self.active_projects) + 1

    @property
    def success_url(self):
        return self.active_year_week.get_absolute_url()

    @property
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
            for index, year_week in enumerate(self.year_weeks_to_display):
                booked = Booking.objects.filter(
                    year_week=year_week,
                    booked_by=self.active_person,
                    booked_on=project).aggregate(
                        models.Sum('hours'))['hours__sum']
                if booked is None:
                    booked = 0
                key = 'hours%s' % index
                line[key] = booked
            line['field'] = fields[project_index]
            result.append(line)
        return result
