from django.views.generic.base import TemplateView


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
