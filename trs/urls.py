from django.conf.urls import include
from django.contrib import admin
from django.urls import re_path
from trs import views


admin.autodiscover()

urlpatterns = [
    re_path(r"^$", views.home, name="trs.home"),
    re_path(r"", include("lizard_auth_client.urls")),
    re_path(
        r"^simple-search/$",
        views.SearchView.as_view(),
        name="trs.search",
    ),
    re_path(r"^persons/$", views.PersonsView.as_view(), name="trs.persons"),
    re_path(r"^persons/csv/$", views.PersonsCsvView.as_view(), name="trs.persons.csv"),
    re_path(r"^persons/(?P<pk>\d+)/$", views.PersonView.as_view(), name="trs.person"),
    re_path(
        r"^persons/(?P<pk>\d+)/kpi/$",
        views.PersonKPIView.as_view(),
        name="trs.person.kpi",
    ),
    re_path(
        r"^persons/(?P<pk>\d+)/edit/$",
        views.PersonEditView.as_view(),
        name="trs.person.edit",
    ),
    re_path(
        r"^persons/(?P<pk>\d+)/edit_target/$",
        views.PersonChangeView.as_view(),
        name="trs.person.target",
    ),
    re_path(r"^projects/$", views.ProjectsView.as_view(), name="trs.projects"),
    re_path(
        r"^projects/loss/$", views.ProjectsLossView.as_view(), name="trs.projects.loss"
    ),
    re_path(
        r"^projects/csv/$", views.ProjectsCsvView.as_view(), name="trs.projects.csv"
    ),
    re_path(
        r"^projects/new/$", views.ProjectCreateView.as_view(), name="trs.project.new"
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/$", views.ProjectView.as_view(), name="trs.project"
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/csv/$",
        views.ProjectCsvView.as_view(),
        name="trs.project.csv",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/persons/csv/$",
        views.ProjectPersonsCsvView.as_view(),
        name="trs.project.persons.csv",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/edit/$",
        views.ProjectEditView.as_view(),
        name="trs.project.edit",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/editremarks/$",
        views.ProjectRemarksEditView.as_view(),
        name="trs.project.editremarks",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/budget/$",
        views.ProjectBudgetEditView.as_view(),
        name="trs.project.budget",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/team-update/$",
        views.TeamUpdateView.as_view(),
        name="trs.project.update-team",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/invoice-delete/(?P<invoice_pk>\d+)/$",
        views.InvoiceDeleteView.as_view(),
        name="trs.project.invoice-delete",
    ),
    re_path(
        r"^projects/(?P<project_pk>\d+)/add_invoice/$",
        views.InvoiceCreateView.as_view(),
        name="trs.invoice.add",
    ),
    re_path(
        r"^projects/(?P<project_pk>\d+)/invoices/(?P<pk>\d+)/$",
        views.InvoiceEditView.as_view(),
        name="trs.invoice.edit",
    ),
    re_path(
        r"^projects/(?P<project_pk>\d+)/add_payable/$",
        views.PayableCreateView.as_view(),
        name="trs.payable.add",
    ),
    re_path(
        r"^projects/(?P<project_pk>\d+)/payables/(?P<pk>\d+)/$",
        views.PayableEditView.as_view(),
        name="trs.payable.edit",
    ),
    re_path(
        r"^projects/(?P<pk>\d+)/payable-delete/(?P<payable_pk>\d+)/$",
        views.PayableDeleteView.as_view(),
        name="trs.project.payable-delete",
    ),
    re_path(r"^booking/$", views.BookingView.as_view(), name="trs.booking"),
    re_path(
        r"^persons/(?P<pk>\d+)/booking/$",
        views.BookingView.as_view(),
        name="trs.booking",
    ),
    re_path(
        r"^persons/(?P<pk>\d+)/booking/(?P<year>\d\d\d\d)-(?P<week>\d\d)/$",
        views.BookingView.as_view(),
        name="trs.booking",
    ),
    # The one below is for single-digit week numbers. There's surely a better
    # way to do this with a regex... [Reinout]
    re_path(
        r"^persons/(?P<pk>\d+)/booking/(?P<year>\d\d\d\d)-0(?P<week>\d)/$",
        views.BookingView.as_view(),
        name="trs.booking",
    ),
    # A PK has no dashes, so it doesn't conflict with the above two regexes.
    re_path(
        r"^persons/(?P<pk>\d+)/bookingoverview/$",
        views.BookingOverview.as_view(),
        name="trs.booking.overview",
    ),
    re_path(
        r"^overviews/wbso_projects/(?P<pk>\d+)/$",
        views.WbsoProjectView.as_view(),
        name="trs.wbso_project",
    ),
    re_path(
        r"^overviews/wbso_projects/csv/$",
        views.WbsoCsvView.as_view(),
        name="trs.wbso.csv",
    ),
    re_path(
        r"^overviews/financial_csv/$",
        views.FinancialCsvView.as_view(),
        name="trs.financial.csv",
    ),
    re_path(
        r"^overviews/financial_csv/(?P<pk>\d+)/$",
        views.FinancialCsvView.as_view(),
        name="trs.financial.csv",
    ),
    re_path(
        r"^overviews/combined_financial_csv/$",
        views.CombinedFinancialCsvView.as_view(),
        name="trs.combined_financial.csv",
    ),
    # Overviews
    re_path(r"^overviews/$", views.OverviewsView.as_view(), name="trs.overviews"),
    re_path(
        r"^overviews/invoices/$",
        views.InvoicesView.as_view(),
        name="trs.overviews.invoices",
    ),
    re_path(
        r"^overviews/project_leaders_and_managers/$",
        views.ProjectLeadersAndManagersView.as_view(),
        name="trs.overviews.pl_pm",
    ),
    re_path(
        r"^overviews/changes/$",
        views.ChangesOverview.as_view(),
        name="trs.overviews.changes",
    ),
    re_path(
        r"^overviews/reservations/$",
        views.ReservationsOverview.as_view(),
        name="trs.overviews.reservations",
    ),
    re_path(
        r"^overviews/invoices_per_month/$",
        views.InvoicesPerMonthOverview.as_view(),
        name="trs.overviews.invoices_per_month",
    ),
    re_path(
        r"^overviews/wbso_projects/$",
        views.WbsoProjectsOverview.as_view(),
        name="trs.overviews.wbso_projects",
    ),
    re_path(
        r"^overviews/payables/$",
        views.PayablesView.as_view(),
        name="trs.overviews.payables",
    ),
    re_path(
        r"^overviews/payables_csv/$",
        views.PayablesCsvView.as_view(),
        name="trs.overviews.payables.csv",
    ),
    re_path(
        r"^overviews/ratings/$",
        views.RatingsOverview.as_view(),
        name="trs.overviews.ratings",
    ),
    re_path(
        r"^overviews/financial/$",
        views.FinancialOverview.as_view(),
        name="trs.overviews.financial",
    ),
    re_path(r"^locallogin/$", views.LoginView.as_view(), name="trs.login"),
    re_path(r"^logout/$", views.logout_view, name="trs.logout"),
    re_path(r"^admin/", admin.site.urls),
]
