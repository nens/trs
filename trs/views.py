import datetime
import logging

from django.views.generic.base import TemplateView

from trs import models

logger = logging.getLogger()


class BaseView(TemplateView):
    template_name = 'trs/base.html'
    title = "TRS tijdregistratiesysteem"

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
    def active_year_week(self):
        from_url = self.kwargs.get('year_and_week')
        if from_url:
            return from_url
        today = datetime.date.today()
        return year_and_week_from_date(today)
