from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin

from trs import views

admin.autodiscover()

urlpatterns = patterns(
    "",
    url(r"^$", views.home, name="trs.home"),
    url(r"", include("lizard_auth_client.urls")),

    url(
        r"^simple-search/$",
        views.SearchView.as_view(),
        name="trs.search",
    ),

    url(r"^persons/$", views.PersonsView.as_view(), name="trs.persons"),
    url(r"^persons/csv/$", views.PersonsCsvView.as_view(), name="trs.persons.csv"),
    url(r"^persons/(?P<pk>\d+)/$", views.PersonView.as_view(), name="trs.person"),
    url(
        r"^persons/(?P<pk>\d+)/kpi/$",
        views.PersonKPIView.as_view(),
        name="trs.person.kpi",
    ),
    url(
        r"^persons/(?P<pk>\d+)/edit/$",
        views.PersonEditView.as_view(),
        name="trs.person.edit",
    ),
    url(
        r"^persons/(?P<pk>\d+)/edit_target/$",
        views.PersonChangeView.as_view(),
        name="trs.person.target",
    ),
    url(r"^projects/$", views.ProjectsView.as_view(), name="trs.projects"),
    url(
        r"^projects/loss/$", views.ProjectsLossView.as_view(), name="trs.projects.loss"
    ),
    url(r"^projects/csv/$", views.ProjectsCsvView.as_view(), name="trs.projects.csv"),
    url(r"^projects/new/$", views.ProjectCreateView.as_view(), name="trs.project.new"),
    url(r"^projects/(?P<pk>\d+)/$", views.ProjectView.as_view(), name="trs.project"),
    url(
        r"^projects/(?P<pk>\d+)/csv/$",
        views.ProjectCsvView.as_view(),
        name="trs.project.csv",
    ),
    url(
        r"^projects/(?P<pk>\d+)/persons/csv/$",
        views.ProjectPersonsCsvView.as_view(),
        name="trs.project.persons.csv",
    ),
    url(
        r"^projects/(?P<pk>\d+)/edit/$",
        views.ProjectEditView.as_view(),
        name="trs.project.edit",
    ),
    url(
        r"^projects/(?P<pk>\d+)/editremarks/$",
        views.ProjectRemarksEditView.as_view(),
        name="trs.project.editremarks",
    ),
    url(
        r"^projects/(?P<pk>\d+)/budget/$",
        views.ProjectBudgetEditView.as_view(),
        name="trs.project.budget",
    ),
    url(
        r"^projects/(?P<pk>\d+)/team-update/$",
        views.TeamUpdateView.as_view(),
        name="trs.project.update-team",
    ),
    url(
        r"^projects/(?P<pk>\d+)/invoice-delete/(?P<invoice_pk>\d+)/$",
        views.InvoiceDeleteView.as_view(),
        name="trs.project.invoice-delete",
    ),
    url(
        r"^projects/(?P<project_pk>\d+)/add_invoice/$",
        views.InvoiceCreateView.as_view(),
        name="trs.invoice.add",
    ),
    url(
        r"^projects/(?P<project_pk>\d+)/invoices/(?P<pk>\d+)/$",
        views.InvoiceEditView.as_view(),
        name="trs.invoice.edit",
    ),
    url(
        r"^projects/(?P<project_pk>\d+)/add_payable/$",
        views.PayableCreateView.as_view(),
        name="trs.payable.add",
    ),
    url(
        r"^projects/(?P<project_pk>\d+)/payables/(?P<pk>\d+)/$",
        views.PayableEditView.as_view(),
        name="trs.payable.edit",
    ),
    url(
        r"^projects/(?P<pk>\d+)/payable-delete/(?P<payable_pk>\d+)/$",
        views.PayableDeleteView.as_view(),
        name="trs.project.payable-delete",
    ),
    url(r"^booking/$", views.BookingView.as_view(), name="trs.booking"),
    url(
        r"^persons/(?P<pk>\d+)/booking/$",
        views.BookingView.as_view(),
        name="trs.booking",
    ),
    url(
        r"^persons/(?P<pk>\d+)/booking/(?P<year>\d\d\d\d)-(?P<week>\d\d)/$",
        views.BookingView.as_view(),
        name="trs.booking",
    ),
    # The one below is for single-digit week numbers. There's surely a better
    # way to do this with a regex... [Reinout]
    url(
        r"^persons/(?P<pk>\d+)/booking/(?P<year>\d\d\d\d)-0(?P<week>\d)/$",
        views.BookingView.as_view(),
        name="trs.booking",
    ),
    # A PK has no dashes, so it doesn't conflict with the above two regexes.
    url(
        r"^persons/(?P<pk>\d+)/bookingoverview/$",
        views.BookingOverview.as_view(),
        name="trs.booking.overview",
    ),
    url(
        r"^overviews/wbso_projects/(?P<pk>\d+)/$",
        views.WbsoProjectView.as_view(),
        name="trs.wbso_project",
    ),
    url(
        r"^overviews/wbso_projects/csv/$",
        views.WbsoCsvView.as_view(),
        name="trs.wbso.csv",
    ),
    url(
        r"^overviews/financial_csv/$",
        views.FinancialCsvView.as_view(),
        name="trs.financial.csv",
    ),
    url(
        r"^overviews/financial_csv/(?P<pk>\d+)/$",
        views.FinancialCsvView.as_view(),
        name="trs.financial.csv",
    ),
    url(
        r"^overviews/combined_financial_csv/$",
        views.CombinedFinancialCsvView.as_view(),
        name="trs.combined_financial.csv",
    ),
    # Overviews
    url(r"^overviews/$", views.OverviewsView.as_view(), name="trs.overviews"),
    url(
        r"^overviews/invoices/$",
        views.InvoicesView.as_view(),
        name="trs.overviews.invoices",
    ),
    url(
        r"^overviews/project_leaders_and_managers/$",
        views.ProjectLeadersAndManagersView.as_view(),
        name="trs.overviews.pl_pm",
    ),
    url(
        r"^overviews/changes/$",
        views.ChangesOverview.as_view(),
        name="trs.overviews.changes",
    ),
    url(
        r"^overviews/reservations/$",
        views.ReservationsOverview.as_view(),
        name="trs.overviews.reservations",
    ),
    url(
        r"^overviews/invoices_per_month/$",
        views.InvoicesPerMonthOverview.as_view(),
        name="trs.overviews.invoices_per_month",
    ),
    url(
        r"^overviews/wbso_projects/$",
        views.WbsoProjectsOverview.as_view(),
        name="trs.overviews.wbso_projects",
    ),
    url(
        r"^overviews/payables/$",
        views.PayablesView.as_view(),
        name="trs.overviews.payables",
    ),
    url(
        r"^overviews/payables_csv/$",
        views.PayablesCsvView.as_view(),
        name="trs.overviews.payables.csv",
    ),
    url(
        r"^overviews/ratings/$",
        views.RatingsOverview.as_view(),
        name="trs.overviews.ratings",
    ),
    url(
        r"^overviews/financial/$",
        views.FinancialOverview.as_view(),
        name="trs.overviews.financial",
    ),
    url(r"^locallogin/$", views.LoginView.as_view(), name="trs.login"),
    url(r"^logout/$", views.logout_view, name="trs.logout"),
    (r"^search/", include("haystack.urls")),
    (r"^admin/", include(admin.site.urls)),
)
