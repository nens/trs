from django.contrib import admin

from trs import models


class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]


class MPCAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]


class PersonAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "group",
        "archived",
        "user",
        "is_office_management",
        "is_management",
    ]
    list_editable = ["group", "archived", "is_office_management"]
    list_filter = ["archived", "group", "is_management", "is_office_management"]
    search_fields = ["name"]


class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "description",
        "group",
        "mpc",
        "wbso_project",
        "wbso_percentage",
        "internal",
        "archived",
    ]
    list_filter = ["internal", "archived", "group", "mpc", "wbso_project"]
    list_editable = ["group", "mpc", "wbso_project", "wbso_percentage"]
    search_fields = ["code", "description"]


class WbsoProjectAdmin(admin.ModelAdmin):
    list_display = ["number", "title", "start_date", "end_date"]
    search_fields = ["title"]
    list_editable = ["title"]


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["number", "project", "date", "description", "amount_exclusive"]
    search_fields = ["number", "project", "description"]
    ordering = ("-date", "-number")  # Reverse from the normal display


class PersonChangeAdmin(admin.ModelAdmin):
    list_display = ["__str__", "year_week"]


class BookingAdmin(admin.ModelAdmin):
    list_display = ["year_week", "hours", "booked_by", "booked_on"]
    list_filter = ["booked_by", "booked_on", "year_week__year"]


class WorkAssignmentAdmin(admin.ModelAdmin):
    list_display = ["assigned_on", "year_week", "assigned_to", "hours", "hourly_tariff"]
    search_fields = ["assigned_on__code", "assigned_to__name"]
    ordering = ["assigned_on", "year_week", "added"]


class BudgetItemAdmin(admin.ModelAdmin):
    pass


class YearWeekAdmin(admin.ModelAdmin):
    # This one can be removed later on.
    pass


class ThirdPartyEstimateAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Group, GroupAdmin)
admin.site.register(models.MPC, MPCAdmin)
admin.site.register(models.Person, PersonAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.WbsoProject, WbsoProjectAdmin)
admin.site.register(models.Invoice, InvoiceAdmin)
admin.site.register(models.PersonChange, PersonChangeAdmin)
admin.site.register(models.Booking, BookingAdmin)
admin.site.register(models.WorkAssignment, WorkAssignmentAdmin)
admin.site.register(models.BudgetItem, BudgetItemAdmin)
admin.site.register(models.YearWeek, YearWeekAdmin)
admin.site.register(models.ThirdPartyEstimate, ThirdPartyEstimateAdmin)
