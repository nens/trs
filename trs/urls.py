from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url

from trs import views


urlpatterns = patterns(
    '',
    url(r'^$',
        views.HomeView.as_view(),
        name='trs.home'),
    )
