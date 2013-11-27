from django.contrib import admin

from trs import models


class PersonAdmin(admin.ModelAdmin):
    pass


class ProjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'internal', 'description']


class PersonChangeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'year_week']


class BookingAdmin(admin.ModelAdmin):
    list_display = ['year_week', 'hours', 'booked_by', 'booked_on']
    list_filter = ['booked_by', 'booked_on']


class WorkAssignmentAdmin(admin.ModelAdmin):
    pass


class BudgetAssignmentAdmin(admin.ModelAdmin):
    pass


class YearWeekAdmin(admin.ModelAdmin):
    # This one can be removed later on.
    pass


admin.site.register(models.Person, PersonAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.PersonChange, PersonChangeAdmin)
admin.site.register(models.Booking, BookingAdmin)
admin.site.register(models.WorkAssignment, WorkAssignmentAdmin)
admin.site.register(models.BudgetAssignment, BudgetAssignmentAdmin)
admin.site.register(models.YearWeek, YearWeekAdmin)
