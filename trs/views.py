import datetime
import logging

from django.views.generic.base import TemplateView

from trs import models

logger = logging.getLogger()


class BaseView(TemplateView):
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
        persons = models.Person.objects.filter(user=self.request.user)
        if persons:
            person = persons[0]
            logger.debug("Found active person: {}", person)
            return person

    @property
    def active_projects(self):
        # TODO: extra filtering for projects that are past their date.
        if not self.active_person:
            return
        return models.Project.objects.filter(
            work_assignments__assigned_to=self.active_person)


class HomeView(BaseView):
    template_name = 'trs/home.html'


class PersonsView(BaseView):
    template_name = 'trs/persons.html'

    @property
    def persons(self):
        return models.Person.objects.all()


class PersonView(BaseView):
    template_name = 'trs/person.html'

    @property
    def person(self):
        return models.Person.objects.get(slug=self.kwargs['slug'])


class ProjectsView(BaseView):
    template_name = 'trs/projects.html'

    @property
    def projects(self):
        return models.Project.objects.all()


class ProjectView(BaseView):
    template_name = 'trs/project.html'

    @property
    def project(self):
        return models.Project.objects.get(slug=self.kwargs['slug'])


class BookingView(BaseView):
    # TODO: also allow /booking/yyyy-ww/ format.
    template_name = 'trs/booking.html'

    @property
    def active_first_day(self):
        year = self.kwargs.get('year')
        week = self.kwargs.get('week')
        if year is not None:  # (Week is also not None, then)
            return models.YearWeek.objects.get(year=year, week=week).first_day
        # Default: this week's first day.
        this_year_week = models.YearWeek.objects.filter(
            first_day__lte=self.today).last()
        return this_year_week.first_day

    @property
    def year_weeks_to_display(self):
        """Return the active YearWeek and the two previous ones."""
        end = self.active_first_day + datetime.timedelta(days=7)
        start = self.active_first_day - datetime.timedelta(days=2 * 7)
        return models.YearWeek.objects.filter(first_day__lte=end).filter(
            first_day__gte=start)
