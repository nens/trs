from django.contrib import admin
from django.urls import include, path, re_path
from nens_auth_client.urls import override_admin_auth

from trs import views

admin.autodiscover()

urlpatterns = [
    path("", views.home, name="trs.home"),
    path("accounts/", include("nens_auth_client.urls", namespace="auth")),
    path(
        "simple-search/",
        views.SearchView.as_view(),
        name="trs.search",
    ),
    path("persons/", views.PersonsView.as_view(), name="trs.persons"),
    path("persons/excel/", views.PersonsExcelView.as_view(), name="trs.persons.excel"),
    path("persons/<int:pk>/", views.PersonView.as_view(), name="trs.person"),
    path(
        "persons/<int:pk>/kpi/",
        views.PersonKPIView.as_view(),
        name="trs.person.kpi",
    ),
    path(
        "persons/<int:pk>/edit/",
        views.PersonEditView.as_view(),
        name="trs.person.edit",
    ),
    path(
        "persons/<int:pk>/edit_target/",
        views.PersonChangeView.as_view(),
        name="trs.person.target",
    ),
    path("projects/", views.ProjectsView.as_view(), name="trs.projects"),
    path("projects/loss/", views.ProjectsLossView.as_view(), name="trs.projects.loss"),
    path(
        "projects/excel/",
        views.ProjectsExcelView.as_view(),
        name="trs.projects.excel",
    ),
    path("projects/new/", views.ProjectCreateView.as_view(), name="trs.project.new"),
    path("projects/<int:pk>/", views.ProjectView.as_view(), name="trs.project"),
    path(
        "projects/<int:pk>/excel/",
        views.ProjectExcelView.as_view(),
        name="trs.project.excel",
    ),
    path(
        "projects/<int:pk>/persons/excel/",
        views.ProjectPersonsExcelView.as_view(),
        name="trs.project.persons.excel",
    ),
    path(
        "projects/<int:pk>/edit/",
        views.ProjectEditView.as_view(),
        name="trs.project.edit",
    ),
    path(
        "projects/<int:pk>/editremarks/",
        views.ProjectRemarksEditView.as_view(),
        name="trs.project.editremarks",
    ),
    path(
        "projects/<int:pk>/budget/",
        views.ProjectBudgetEditView.as_view(),
        name="trs.project.budget",
    ),
    path(
        "projects/<int:pk>/team-update/",
        views.TeamUpdateView.as_view(),
        name="trs.project.update-team",
    ),
    path(
        "projects/<int:pk>/invoice-delete/<int:invoice_pk>/",
        views.InvoiceDeleteView.as_view(),
        name="trs.project.invoice-delete",
    ),
    path(
        "projects/<int:project_pk>/add_invoice/",
        views.InvoiceCreateView.as_view(),
        name="trs.invoice.add",
    ),
    path(
        "projects/<int:project_pk>/invoices/<int:pk>/",
        views.InvoiceEditView.as_view(),
        name="trs.invoice.edit",
    ),
    path(
        "projects/<int:project_pk>/add_payable/",
        views.PayableCreateView.as_view(),
        name="trs.payable.add",
    ),
    path(
        "projects/<int:project_pk>/payables/<int:pk>/",
        views.PayableEditView.as_view(),
        name="trs.payable.edit",
    ),
    path(
        "projects/<int:pk>/payable-delete/<int:payable_pk>/",
        views.PayableDeleteView.as_view(),
        name="trs.project.payable-delete",
    ),
    path("booking/", views.BookingView.as_view(), name="trs.booking"),
    path(
        "persons/<int:pk>/booking/",
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
    path(
        "persons/<int:pk>/bookingoverview/",
        views.BookingOverview.as_view(),
        name="trs.booking.overview",
    ),
    path(
        "persons/<int:pk>/freeoverview/",
        views.FreeOverview.as_view(),
        name="trs.booking.free-overview",
    ),
    path(
        "overviews/wbso_projects/<int:pk>/",
        views.WbsoProjectView.as_view(),
        name="trs.wbso_project",
    ),
    path(
        "overviews/wbso_projects/excel/",
        views.WbsoExcelView.as_view(),
        name="trs.wbso.excel",
    ),
    path(
        "overviews/wbso_projects/excel2/",
        views.WbsoExcelView2.as_view(),
        name="trs.wbso.excel2",
    ),
    path(
        "overviews/financial_excel/",
        views.FinancialExcelView.as_view(),
        name="trs.financial.excel",
    ),
    # The next two differentiate in their pk.
    path(
        "overviews/financial_excel/group/<int:group_pk>/",
        views.FinancialExcelView.as_view(),
        name="trs.financial.excel",
    ),
    path(
        "overviews/financial_excel/mpc/<int:mpc_pk>/",
        views.FinancialExcelView.as_view(),
        name="trs.financial.excel",
    ),
    path(
        "overviews/combined_financial_excel/",
        views.CombinedFinancialExcelView.as_view(),
        name="trs.combined_financial.excel",
    ),
    # Overviews
    path("overviews/", views.OverviewsView.as_view(), name="trs.overviews"),
    path(
        "overviews/invoices/",
        views.InvoicesView.as_view(),
        name="trs.overviews.invoices",
    ),
    path(
        "overviews/project_leaders_and_managers/",
        views.ProjectLeadersAndManagersView.as_view(),
        name="trs.overviews.pl_pm",
    ),
    path(
        "overviews/changes/",
        views.ChangesOverview.as_view(),
        name="trs.overviews.changes",
    ),
    path(
        "overviews/reservations/",
        views.ReservationsOverview.as_view(),
        name="trs.overviews.reservations",
    ),
    path(
        "overviews/invoices_per_month/",
        views.InvoicesPerMonthOverview.as_view(),
        name="trs.overviews.invoices_per_month",
    ),
    path(
        "overviews/wbso_projects/",
        views.WbsoProjectsOverview.as_view(),
        name="trs.overviews.wbso_projects",
    ),
    path(
        "overviews/payables/",
        views.PayablesView.as_view(),
        name="trs.overviews.payables",
    ),
    path(
        "overviews/payables_excel/",
        views.PayablesExcelView.as_view(),
        name="trs.overviews.payables.excel",
    ),
    path(
        "overviews/ratings/",
        views.RatingsOverview.as_view(),
        name="trs.overviews.ratings",
    ),
    path(
        "overviews/financial/",
        views.FinancialOverview.as_view(),
        name="trs.overviews.financial",
    ),
    path("locallogin/", views.LoginView.as_view(), name="trs.login"),
    path("logout/", views.logout_view, name="trs.logout"),
    *override_admin_auth(),
    re_path(r"^admin/", admin.site.urls),
]
