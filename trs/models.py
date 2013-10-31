import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

# TODO: add setting ADMIN_USER_CAN_DELETE_PERSONS_AND_PROJECTS
# TODO: add django-appconf

# Hours are always an integer. You cannot work 2.5 hours. At least, that's
# what they assure me right now. I'm only 60% sure that it stays that way, so
# I use DecimalField instead of IntegerField. I want to use it for targets,
# too. 999999.99 should be possible, so that's 8 digits with 2 decimal places.
MAX_DIGITS = 8
DECIMAL_PLACES = 2
YYYY_WW_FORMAT = re.compile(r"\d\d\d\d-\d\d")


def is_year_and_week_format(value):
    """Raise ValidationError when the value isn't in the yyyy-ww format."""
    if not YYYY_WW_FORMAT.match(value):
        raise ValidationError("Value not in yyyy-ww format")
    parts = value.split('-')
    week = int(parts[1])
    if week < 0 or week > 53:
        raise ValidationError("Week should be 0-53 (inclusive)")


class Person(models.Model):
    name = models.CharField(
        verbose_name="naam",
        max_length=255)
    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        verbose_name="gebruiker",
        # TODO: make unique.
        help_text="De interne (django) gebruiker die deze persoon is.")
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

    def get_absolute_url(self):
        return reverse('trs.person', kwargs={'slug': self.slug})

    def as_widget(self):
        return mark_safe(render_to_string('trs/person-widget.html',
                                          {'person': self}))

    def hours_per_week(self):
        return self.person_changes.all().aggregate(
            models.Sum('hours_per_week'))['hours_per_week__sum']

    def target(self):
        return self.person_changes.all().aggregate(
            models.Sum('target'))['target__sum']


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

    def get_absolute_url(self):
        return reverse('trs.project', kwargs={'slug': self.slug})

    def as_widget(self):
        return mark_safe(render_to_string('trs/project-widget.html',
                                          {'project': self}))


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
    year_and_week = models.CharField(
        max_length=7,  # yyyy-ww
        db_index=True,
        verbose_name="jaar en week",
        validators=[is_year_and_week_format])

    class Meta:
        abstract = True
        ordering = ['year_and_week', 'added']


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

    person = models.ForeignKey(
        Person,
        blank=True,
        null=True,
        verbose_name="persoon",
        help_text="persoon waar de verandering voor is",
        related_name="person_changes")

    class Meta:
        verbose_name = "verandering aan persoon"
        verbose_name_plural = "veranderingen aan personen"


class Booking(EventBase):
    hours = models.DecimalField(
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        blank=True,
        null=True,
        verbose_name="uren")

    booked_by = models.ForeignKey(
        Person,
        blank=True,
        null=True,
        verbose_name="geboekd door",
        related_name="bookings")
    booked_on = models.ForeignKey(
        Project,
        blank=True,
        null=True,
        verbose_name="geboekd op",
        related_name="bookings")

    class Meta:
        verbose_name = "boeking"
        verbose_name_plural = "boekingen"


class WorkAssignment(EventBase):
    hours = models.DecimalField(
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        blank=True,
        null=True,
        verbose_name="uren")
    hourly_tariff = models.DecimalField(
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        blank=True,
        null=True,
        verbose_name="uurtarief")

    assigned_on = models.ForeignKey(
        Project,
        blank=True,
        null=True,
        verbose_name="toegekend voor",
        related_name="work_assignments")
    assigned_to = models.ForeignKey(
        Person,
        blank=True,
        null=True,
        verbose_name="toegekend aan",
        related_name="work_assignments")

    class Meta:
        verbose_name = "toekenning van werk"
        verbose_name_plural = "toekenningen van werk"


class BudgetAssignment(EventBase):
    budget = models.DecimalField(
        max_digits=12,  # We don't mind a metric ton of hard cash.
        decimal_places=DECIMAL_PLACES,
        blank=True,
        null=True,
        verbose_name="uren")
    # TODO: link to doc or so

    assigned_to = models.ForeignKey(
        Project,
        blank=True,
        null=True,
        verbose_name="toegekend aan",
        related_name="budget_assignments")

    class Meta:
        verbose_name = "toekenning van budget"
        verbose_name_plural = "toekenningen van budget"
