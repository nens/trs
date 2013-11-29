import datetime
import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from tls import request as tls_request

# TODO: add setting TRS_ADMIN_USER_CAN_DELETE_PERSONS_AND_PROJECTS
# TODO: add django-appconf

# Hours are always an integer. You cannot work 2.5 hours. At least, that's
# what they assure me right now. I'm only 60% sure that it stays that way, so
# I use DecimalField instead of IntegerField. I want to use it for targets,
# too. 999999.99 should be possible, so that's 8 digits with 2 decimal places.
MAX_DIGITS = 8
DECIMAL_PLACES = 2

logger = logging.getLogger(__name__)


def this_year_week():
    return YearWeek.objects.filter(
        first_day__lte=datetime.date.today()).last()


def last_four_year_weeks():
    result = list(YearWeek.objects.filter(
        first_day__lte=datetime.date.today()).reverse()[1:5])
    result.reverse()  # In-place...
    return result


class Person(models.Model):
    name = models.CharField(
        verbose_name="naam",
        max_length=255)
    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        verbose_name="gebruiker",
        unique=True,
        help_text="De interne (django) gebruiker die deze persoon is.")
    login_name = models.CharField(
        verbose_name="inlognaam bij N&S",
        max_length=255,
        help_text="Dit is dus het eerste deel van het emailadres.")
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
    # Description on persons is useful for noting that someone doesn't work
    # for us anymore, for instance. And other corner cases.
    is_office_management = models.BooleanField(
        verbose_name="office management",
        help_text="Office management can edit and add everything",
        default=False)
    is_management = models.BooleanField(
        verbose_name="management",
        help_text=("Management can see everything, but doesn't get extra " +
                   "edit rights"),
        default=False)

    class Meta:
        verbose_name = "persoon"
        verbose_name_plural = "personen"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('trs.person', kwargs={'pk': self.pk})

    def as_widget(self):
        return mark_safe(render_to_string('trs/person-widget.html',
                                          {'person': self}))

    def hours_per_week(self, year_week=None):
        if year_week is None:
            year_week = this_year_week()
        return self.person_changes.filter(
            year_week__lte=year_week).aggregate(
                models.Sum('hours_per_week'))['hours_per_week__sum'] or 0

    def standard_hourly_tariff(self, year_week=None):
        if year_week is None:
            year_week = this_year_week()
        return self.person_changes.filter(
            year_week__lte=year_week).aggregate(
                models.Sum('standard_hourly_tariff'))[
                    'standard_hourly_tariff__sum'] or 0

    def external_percentage(self, year_week=None):
        if year_week is None:
            year_week = this_year_week()
        return self.person_changes.filter(
            year_week__lte=year_week).aggregate(
                models.Sum('external_percentage'))[
                    'external_percentage__sum'] or 0

    def target(self, year_week=None):
        if year_week is None:
            year_week = this_year_week()
        return self.person_changes.filter(
            year_week__lte=year_week).aggregate(
                models.Sum('target'))['target__sum'] or 0

    def assigned_projects(self):
        return Project.objects.filter(
            work_assignments__assigned_to=self).distinct()

    def booking_percentage(self):
        weeks = last_four_year_weeks()
        hours_to_work = sum([self.hours_per_week(year_week=week)
                         for week in weeks])
        booked_in_weeks = self.bookings.filter(year_week__in=weeks).aggregate(
            models.Sum('hours'))['hours__sum'] or 0
        if not hours_to_work:
            # Prevent division by zero.
            return 100
        # TODO: het onderstaande klopt niet!
        return round(100 * booked_in_weeks / hours_to_work)

    def external_internal_ratio(self):
        internal = 100 - self.external_percentage()
        return "%s/%s" % (self.external_percentage(), internal)


class Project(models.Model):
    code = models.CharField(
        verbose_name="projectcode",
        max_length=255)
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
    added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="toegevoegd op")
    internal = models.BooleanField(
        verbose_name="intern project",
        default=False)
    principal = models.CharField(
        verbose_name="opdrachtgever",
        blank=True,
        max_length=255)
    start = models.ForeignKey(
        'YearWeek',
        blank=True,
        null=True,
        related_name="starting_projects",
        verbose_name="startweek")
    end = models.ForeignKey(
        'YearWeek',
        blank=True,
        null=True,
        related_name="ending_projects",
        verbose_name="laatste week")
    project_leader = models.ForeignKey(
        Person,
        blank=True,
        null=True,
        verbose_name="projectleider",
        help_text="verantwoordelijke voor de uren op het project",
        related_name="projects_i_lead")
    project_manager = models.ForeignKey(
        Person,
        blank=True,
        null=True,
        verbose_name="projectmanager",
        help_text="verantwoordelijke voor het budget van het project",
        related_name="projects_i_manage")
    is_accepted = models.BooleanField(
        verbose_name="goedgekeurd",
        help_text=("Project is goedgekeurd door PM en PL en kan qua team " +
                   "en budgetverdeling niet meer gewijzigd worden."),
        default=False)

    class Meta:
        verbose_name = "project"
        verbose_name_plural = "projecten"
        ordering = ('internal', 'code')

    def __str__(self):
        return self.code

    def get_absolute_url(self):
        return reverse('trs.project', kwargs={'pk': self.pk})

    def as_widget(self):
        return mark_safe(render_to_string('trs/project-widget.html',
                                          {'project': self}))

    def assigned_persons(self):
        return Person.objects.filter(
            work_assignments__assigned_on=self).distinct()

    def budget(self):
        return self.budget_assignments.all().aggregate(
            models.Sum('budget'))['budget__sum'] or 0


class Invoice(models.Model):
    project = models.ForeignKey(
        Project,
        related_name="invoices",
        verbose_name="project")
    date = models.DateField(
        verbose_name="factuurdatum",
        help_text="Formaat: 1972-12-25, jjjj-mm-dd")
    number = models.CharField(
        verbose_name="factuurnummer",
        max_length=255)
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
    amount_exclusive = models.DecimalField(
        max_digits=12,  # We don't mind a metric ton of hard cash.
        decimal_places=DECIMAL_PLACES,
        default=0,
        verbose_name="bedrag exclusief")
    vat = models.DecimalField(
        max_digits=12,
        decimal_places=DECIMAL_PLACES,
        default=0,
        verbose_name="btw")
    payed = models.DateField(
        blank=True,
        null=True,
        verbose_name="betaald op",
        help_text="Formaat: 1972-12-25, jjjj-mm-dd")

    class Meta:
        verbose_name = "factuur"
        verbose_name_plural = "facturen"
        ordering = ('number',)

    def __str__(self):
        return self.number

    def get_absolute_url(self):
        return reverse('trs.invoice.edit', kwargs={'pk': self.pk,
                                                   'project_pk': self.project.pk})

    @property
    def amount_inclusive(self):
        return self.amount_exclusive + self.vat


class YearWeek(models.Model):
    # This ought to be automatically generated.
    year = models.IntegerField(
        verbose_name="jaar")
    week = models.IntegerField(
        verbose_name="weeknummer")
    first_day = models.DateField(
        verbose_name="eerste maandag van de week",
        # Note: 1 january won't always be a monday, that's fine.
        db_index=True)

    class Meta:
        verbose_name = "jaar/week combinatie"
        verbose_name_plural = "jaar/week combinaties"
        ordering = ['year', 'week']

    def __str__(self):
        return "{:04d}-{:02d}".format(self.year, self.week)

    def get_absolute_url(self):
        """Return link to the booking page for this year/week."""
        return reverse('trs.booking', kwargs={'year': self.year,
                                              'week': self.week})

    def as_widget(self):
        return mark_safe(render_to_string('trs/year-week-widget.html',
                                          {'year_week': self}))

    def friendly(self):
        return mark_safe(render_to_string('trs/year-week-friendly.html',
                                          {'year_week': self}))


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
    year_week = models.ForeignKey(
        YearWeek,
        blank=True,
        null=True,
        verbose_name="jaar en week",
        help_text="Ingangsdatum van de wijziging (of datum van de boeking)")

    class Meta:
        abstract = True
        ordering = ['year_and_week', 'added']

    def save(self, *args, **kwargs):
        if not self.year_week:
            self.year_week = this_year_week()
        if not self.added_by:
            if tls_request:
                # If tls_request doesn't exist we're running tests. Adding
                # this 'if' is handier than mocking it the whole time :-)
                self.added_by = tls_request.user
        return super(EventBase, self).save(*args, **kwargs)


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
    standard_hourly_tariff = models.DecimalField(
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        blank=True,
        null=True,
        verbose_name="standaard uurtarief")
    external_percentage = models.IntegerField(
        validators=[MinValueValidator(0),
                    MaxValueValidator(100)],
        blank=True,
        null=True,
        verbose_name="percentage extern")

    person = models.ForeignKey(
        Person,
        blank=True,
        null=True,
        verbose_name="persoon",
        help_text="persoon waar de verandering voor is",
        related_name="person_changes")

    def __str__(self):
        return 'PersonChange on %s' % self.person

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
        verbose_name="geboekt door",
        related_name="bookings")
    booked_on = models.ForeignKey(
        Project,
        blank=True,
        null=True,
        verbose_name="geboekt op",
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
        verbose_name="bedrag")
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
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
