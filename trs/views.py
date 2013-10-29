from django.views.generic.base import TemplateView

from trs import models


class BaseView(TemplateView):
    template_name = 'trs/base.html'
    title = "TRS tijdregistratiesysteem"


class HomeView(BaseView):
    template_name = 'trs/home.html'


class ProjectsView(BaseView):
    """Show project list and individual projects.

    TODO: thinkwork.

    A single page for showing a list and for showing individual projects? Een
    soort deel-single-page-app?

    Then what are the specific things that this view ought to do? Configure
    the overview column, for instance?

    Template snippets klaarzetten?

    => djangorestframework, angularjs :-)

    """
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
