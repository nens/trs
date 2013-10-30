from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin

from trs import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    url(r'^$',
        views.HomeView.as_view(),
        name='trs.home'),
    url(r'^persons/$',
        views.PersonsView.as_view(),
        name='trs.persons'),
    url(r'^persons/(?P<slug>\w+)/$',
        views.PersonView.as_view(),
        name='trs.person'),
    url(r'^projects/$',
        views.ProjectsView.as_view(),
        name='trs.projects'),
    url(r'^projects/(?P<slug>\w+)/$',
        views.ProjectView.as_view(),
        name='trs.project'),
    url(r'^booking/$',
        views.BookingView.as_view(),
        name='trs.booking'),
    )
