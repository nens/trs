from django.db import models
from django.contrib.auth.models import User

# TODO: add setting ADMIN_USER_CAN_DELETE_PERSONS_AND_PROJECTS
# TODO: add django-appconf

# Hours are always an integer. You cannot work 2.5 hours. At least, that's
# what they assure me right now. I'm only 60% sure that it stays that way, so
# I use DecimalField instead of IntegerField. I want to use it for targets,
# too. 999999.99 should be possible, so that's 8 digits with 2 decimal places.
MAX_DIGITS = 8
DECIMAL_PLACES = 2


class Person(models.Model):
    name = models.CharField(
        verbose_name="naam",
        max_length=255)
    login_name = models.CharField(
        verbose_name="inlognaam bij N&S",
        max_length=255,
        help_text="Dit is dus het eerste deel van het emailadres.")
    slug = models.SlugField(
        verbose_name="ID voor in de URL")
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
    # Description on persons is useful for noting that someone doesn't work
    # for us anymore, for instance. And other corner cases.

    class Meta:
        verbose_name = "persoon"
        verbose_name_plural = "personen"
        ordering = ['name']

    def __str__(self):
        return "Person {}".format(self.name)


class Project(models.Model):
    code = models.CharField(
        verbose_name="projectcode",
        max_length=255)
    slug = models.SlugField(
        verbose_name="ID voor in de URL")
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
    added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="toegevoegd op")

    class Meta:
        verbose_name = "project"
        verbose_name_plural = "projecten"
        ordering = ['code']

    def __str__(self):
        return "Project {}".format(self.code)


class EventBase(models.Model):
    added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="toegevoegd op")
    added_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        #editable=False,
        verbose_name="toegevoegd door")
    year = models.IntegerField(
        verbose_name="jaar")
    week = models.IntegerField(
        verbose_name="week")

    class Meta:
        abstract = True
        ordering = ['added']


class PersonChange(EventBase):
    hours_per_week = models.DecimalField(
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        blank=True,
        null=True,
        verbose_name="uren per week")
    target = models.DecimalField(
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        blank=True,
        null=True,
        verbose_name="target")

    class Meta:
        verbose_name = "verandering aan persoon"
        verbose_name_plural = "veranderingen aan personen"
