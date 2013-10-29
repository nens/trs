from django.contrib import admin

from trs import models


class PersonAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('login_name',)}


class ProjectAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('code',)}


class PersonChangeAdmin(admin.ModelAdmin):
    pass


class BookingAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Person, PersonAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.PersonChange, PersonChangeAdmin)
admin.site.register(models.Booking, BookingAdmin)
