from django.contrib import admin

from trs import models


class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'description',]


class PersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'archived', 'user', 'is_office_management',
                    'is_management']
    list_editable = ['archived', 'is_office_management']
    search_fields = ['name']


class ProjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'internal', 'hidden', 'hourless', 'archived',
                    'description']
    list_filter = ['internal', 'archived']
    search_fields = ['code', 'description']


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['number', 'project', 'date', 'description']
    search_fields = ['number', 'project', 'description']


class PersonChangeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'year_week']


class BookingAdmin(admin.ModelAdmin):
    list_display = ['year_week', 'hours', 'booked_by', 'booked_on']
    list_filter = ['booked_by', 'booked_on', 'year_week__year']


class WorkAssignmentAdmin(admin.ModelAdmin):
    pass


class BudgetItemAdmin(admin.ModelAdmin):
    pass


class YearWeekAdmin(admin.ModelAdmin):
    # This one can be removed later on.
    pass


admin.site.register(models.Group, GroupAdmin)
admin.site.register(models.Person, PersonAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.Invoice, InvoiceAdmin)
admin.site.register(models.PersonChange, PersonChangeAdmin)
admin.site.register(models.Booking, BookingAdmin)
admin.site.register(models.WorkAssignment, WorkAssignmentAdmin)
admin.site.register(models.BudgetItem, BudgetItemAdmin)
admin.site.register(models.YearWeek, YearWeekAdmin)
