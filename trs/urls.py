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
    )
