from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin

from trs import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$',
        views.home,
        name='trs.home'),

    url(r'', include('lizard_auth_client.urls')),

    url(r'^persons/$',
        views.PersonsView.as_view(),
        name='trs.persons'),
    url(r'^persons/new/$',
        views.PersonCreateView.as_view(),
        name='trs.person.new'),
    url(r'^persons/(?P<pk>\d+)/$',
        views.PersonView.as_view(),
        name='trs.person'),
    url(r'^persons/(?P<pk>\d+)/kpi/$',
        views.PersonKPIView.as_view(),
        name='trs.person.kpi'),
    url(r'^persons/(?P<pk>\d+)/edit/$',
        views.PersonEditView.as_view(),
        name='trs.person.edit'),
    url(r'^persons/(?P<pk>\d+)/edit_target/$',
        views.PersonChangeView.as_view(),
        name='trs.person.target'),

    url(r'^projects/$',
        views.ProjectsView.as_view(),
        name='trs.projects'),
    url(r'^projects/new/$',
        views.ProjectCreateView.as_view(),
        name='trs.project.new'),
    url(r'^projects/(?P<pk>\d+)/$',
        views.ProjectView.as_view(),
        name='trs.project'),
    url(r'^projects/(?P<pk>\d+)/edit/$',
        views.ProjectEditView.as_view(),
        name='trs.project.edit'),
    url(r'^projects/(?P<pk>\d+)/team/$',
        views.TeamEditView.as_view(),
        name='trs.project.team'),
    url(r'^projects/(?P<pk>\d+)/team-update/$',
        views.TeamUpdateView.as_view(),
        name='trs.project.update-team'),
    url(r'^projects/(?P<pk>\d+)/team-member-delete/(?P<person_pk>\d+)/$',
        views.TeamMemberDeleteView.as_view(),
        name='trs.project.team-member-delete'),
    url(r'^projects/(?P<pk>\d+)/invoice-delete/(?P<invoice_pk>\d+)/$',
        views.InvoiceDeleteView.as_view(),
        name='trs.project.invoice-delete'),
    url(r'^projects/(?P<pk>\d+)/budget-item-delete/(?P<budget_item_pk>\d+)/$',
        views.BudgetItemDeleteView.as_view(),
        name='trs.project.budget-item-delete'),

    url(r'^projects/(?P<project_pk>\d+)/add_invoice/$',
        views.InvoiceCreateView.as_view(),
        name='trs.invoice.add'),
    url(r'^projects/(?P<project_pk>\d+)/invoices/(?P<pk>\d+)/$',
        views.InvoiceEditView.as_view(),
        name='trs.invoice.edit'),
    url(r'^projects/(?P<project_pk>\d+)/add_budget_item/$',
        views.BudgetItemCreateView.as_view(),
        name='trs.budget_item.add'),
    url(r'^projects/(?P<project_pk>\d+)/budget_items/(?P<pk>\d+)/$',
        views.BudgetItemEditView.as_view(),
        name='trs.budget_item.edit'),

    url(r'^booking/$',
        views.BookingView.as_view(),
        name='trs.booking'),
    url(r'^booking/(?P<year>\d\d\d\d)-(?P<week>\d\d)/$',
        views.BookingView.as_view(),
        name='trs.booking'),
    # The one below is for single-digit week numbers. There's surely a better
    # way to do this with a regex... [Reinout]
    url(r'^booking/(?P<year>\d\d\d\d)-0(?P<week>\d)/$',
        views.BookingView.as_view(),
        name='trs.booking'),
    # A PK has no dashes, so it doesn't conflict with the above two regexes.
    url(r'^booking/(?P<pk>\d+)/$',
        views.BookingOverview.as_view(),
        name='trs.booking.overview'),

    # Overviews
    url(r'^overviews/$',
        views.OverviewsView.as_view(),
        name='trs.overviews'),
    url(r'^overviews/invoices/$',
        views.InvoicesView.as_view(),
        name='trs.overviews.invoices'),
    url(r'^overviews/changes/$',
        views.ChangesOverview.as_view(),
        name='trs.overviews.changes'),

    url(r'^locallogin/$',
        views.LoginView.as_view(),
        name='trs.login'),
    url(r'^logout/$',
        views.logout_view,
        name='trs.logout'),

    (r'^admin/', include(admin.site.urls)),
)
