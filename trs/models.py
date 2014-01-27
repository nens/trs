import datetime
import logging
import time

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
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
    cache_key = 'this-year-week2'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = YearWeek.objects.filter(
        first_day__lte=datetime.date.today()).last()
    cache.set(cache_key, result, 3600)
    return result


def cache_per_week(callable):
    # Note: only for PersonChange related fields.
    def inner(self, year_week=None):
        cache_key = self.person_change_cache_key(callable.__name__, year_week)
        result = cache.get(cache_key)
        if result is None:
            result = callable(self, year_week)
            cache.set(cache_key, result)
        return result
    return inner


def cache_on_model(callable):
    def inner(self):
        cache_key = self.cache_key(callable.__name__)
        result = cache.get(cache_key)
        if result is None:
            result = callable(self)
            cache.set(cache_key, result)
        return result
    return inner


def cache_on_model_every_week(callable):
    def inner(self):
        cache_key = self.cache_key(callable.__name__)
        cache_key += this_year_week().as_param()
        result = cache.get(cache_key)
        if result is None:
            result = callable(self)
            cache.set(cache_key, result)
        return result
    return inner


class Group(models.Model):
    name = models.CharField(
        verbose_name="naam",
        max_length=255)
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)

    class Meta:
        verbose_name = "groep"
        verbose_name_plural = "groepen"
        ordering = ['name']

    def __str__(self):
        return self.name


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
        help_text=("De interne (django) gebruiker die deze persoon is. " +
                   "Dit wordt normaliter automatisch gekoppeld op basis van" +
                   "de loginnaam zodra de gebruiker voor de eerste keer " +
                   "inlogt."))
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
    # Description on persons is useful for noting that someone doesn't work
    # for us anymore, for instance. And other corner cases.
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        verbose_name="groep",
        related_name="persons")
    is_office_management = models.BooleanField(
        verbose_name="office management",
        help_text="Office management can edit and add everything",
        default=False)
    is_management = models.BooleanField(
        verbose_name="management",
        help_text=("Management can see everything, but doesn't get extra " +
                   "edit rights"),
        default=False)
    archived = models.BooleanField(
        verbose_name="gearchiveerd",
        default=False)
    cache_indicator = models.IntegerField(
        default=0,
        verbose_name="cache indicator")
    cache_indicator_person_change = models.IntegerField(
        default=0,
        verbose_name="cache indicator voor PersonChange veranderingen")

    class Meta:
        verbose_name = "persoon"
        verbose_name_plural = "personen"
        ordering = ['archived', 'name']

    def save(self, *args, **kwargs):
        self.cache_indicator += 1
        return super(Person, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def cache_key(self, for_what, year_week=None):
        cache_version = 8
        week_id = year_week and year_week.id or this_year_week().id
        return 'person-%s-%s-%s-%s-%s' % (
            self.id, self.cache_indicator, for_what, week_id, cache_version)

    def person_change_cache_key(self, for_what, year_week=None):
        cache_version = 4
        week_id = year_week and year_week.id or this_year_week().id
        return 'person-%s-pc%s-%s-%s-%s' % (
            self.id, self.cache_indicator_person_change, for_what, week_id,
            cache_version)

    def get_absolute_url(self):
        return reverse('trs.person', kwargs={'pk': self.pk})

    def as_widget(self):
        return mark_safe(render_to_string('trs/person-widget.html',
                                          {'person': self}))

    @cache_per_week
    def hours_per_week(self, year_week=None):
        if year_week is None:
            year_week = this_year_week()
        return round(self.person_changes.filter(
            year_week__lte=year_week).aggregate(
                models.Sum('hours_per_week'))['hours_per_week__sum'] or 0)

    @cache_per_week
    def standard_hourly_tariff(self, year_week=None):
        if year_week is None:
            year_week = this_year_week()
        return round(self.person_changes.filter(
            year_week__lte=year_week).aggregate(
                models.Sum('standard_hourly_tariff'))[
                    'standard_hourly_tariff__sum'] or 0)

    @cache_per_week
    def minimum_hourly_tariff(self, year_week=None):
        if year_week is None:
            year_week = this_year_week()
        return round(self.person_changes.filter(
            year_week__lte=year_week).aggregate(
                models.Sum('minimum_hourly_tariff'))[
                    'minimum_hourly_tariff__sum'] or 0)

    @cache_per_week
    def target(self, year_week=None):
        if year_week is None:
            year_week = this_year_week()
        return round(self.person_changes.filter(
            year_week__lte=year_week).aggregate(
                models.Sum('target'))['target__sum'] or 0)

    @cache_on_model
    def filtered_assigned_projects(self):
        return Project.objects.filter(
            work_assignments__assigned_to=self,
            archived=False,
            end__gte=this_year_week()).distinct()

    @cache_on_model
    def assigned_projects(self):
        return Project.objects.filter(
            work_assignments__assigned_to=self).distinct()

    @cache_per_week
    def to_work_up_till_now(self, year_week=None):
        """Return hours I've had to work this year."""
        if year_week is None:
            year_week = this_year_week()
        this_year = year_week.year
        hours_per_week = round(self.person_changes.filter(
            year_week__year__lt=this_year).aggregate(
                models.Sum('hours_per_week'))['hours_per_week__sum'] or 0)
        changes_this_year = self.person_changes.filter(
            year_week__year=this_year,
            year_week__week__lte=year_week.week).values(
                'year_week__week').annotate(
                    models.Sum('hours_per_week'))
        changes_per_week = {change['year_week__week']:
                            round(change['hours_per_week__sum'])
                            for change in changes_this_year}
        result = 0
        # Grab week numbers. "lt" isn't "lte" as we want to exclude the
        # current week. You only have to book on friday!
        year_weeks = YearWeek.objects.filter(
            year=year_week.year,
            week__lt=year_week.week).values('week', 'num_days_missing')
        week_numbers = [item['week'] for item in year_weeks]
        missing_days = sum([item['num_days_missing'] for item in year_weeks])
        for week in week_numbers:
            if week in changes_per_week:
                hours_per_week += changes_per_week[week]
            result += hours_per_week
        result -= missing_days * 8
        # The line above might have pushed it below zero, so compensate:
        return max(0, result)

    @cache_on_model_every_week
    def to_book(self):
        """Return absolute days and weeks (rounded) left to book."""
        this_year = this_year_week().year
        hours_to_work = self.to_work_up_till_now()
        # ^^^ Doesn't include the current week, so we don't count bookings in
        # this week, too.
        booked_this_year = self.bookings.filter(
            year_week__year=this_year,
            year_week__week__lt=this_year_week().week).aggregate(
                models.Sum('hours'))['hours__sum'] or 0
        hours_to_book = max(0, (hours_to_work - booked_this_year))
        days_to_book = round(hours_to_book / 8)  # Assumption: 8 hour workday.
        if self.hours_per_week():
            weeks_to_book = round(hours_to_book / self.hours_per_week())
        else:  # Division by zero
            weeks_to_book = 0

        to_book_this_week = (self.hours_per_week() -
                             8 * this_year_week().num_days_missing)
        booked_this_week = self.bookings.filter(
            year_week=this_year_week()).aggregate(
                models.Sum('hours'))['hours__sum'] or 0
        left_to_book_this_week = to_book_this_week - booked_this_week

        if weeks_to_book > 1:
            klass = 'danger'
            friendly = '%s weken' % weeks_to_book
            short = '%sw' % weeks_to_book
        elif weeks_to_book == 1:
            klass = 'warning'
            friendly = '%s week' % weeks_to_book
            short = '%sw' % weeks_to_book
        elif days_to_book > 1:
            klass = 'warning'
            friendly = '%s dagen' % days_to_book
            short = '%sd' % days_to_book
        elif days_to_book == 1:
            klass = 'warning'
            friendly = '%s dag' % days_to_book
            short = '%sd' % days_to_book
        else:
            klass = 'success'
            friendly = 0
            short = ''
        return {'hours': round(hours_to_book),
                'days': days_to_book,
                'weeks': weeks_to_book,
                'friendly': friendly,
                'short': short,
                'klass': klass,
                'left_to_book_this_week': round(left_to_book_this_week)}


class Project(models.Model):
    code = models.CharField(
        verbose_name="projectcode",
        unique=True,
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
    hidden = models.BooleanField(
        verbose_name="afgeschermd project",
        help_text=("Zet dit standaard aan voor interne projecten, tenzij " +
                   "het een 'echt' project is waar uren voor staan. " +
                   "Afgeschermde projecten kan je andermans gegevens niet " +
                   "van zien. Goed voor ziekte enzo."),
        default=False)
    hourless = models.BooleanField(
        verbose_name="tel uren niet mee",
        help_text=("Uren van dit project tellen niet mee voor de " +
                   "intern/extern verhouding en binnen/buiten budget. " +
                   "Gebruik dit voor verlof en zwangerschapsverlof."),
        default=False)
    archived = models.BooleanField(
        verbose_name="gearchiveerd",
        default=False)
    principal = models.CharField(
        verbose_name="opdrachtgever",
        blank=True,
        max_length=255)
    contract_amount = models.DecimalField(
        max_digits=12,  # We don't mind a metric ton of hard cash.
        decimal_places=DECIMAL_PLACES,
        default=0,
        verbose_name="opdrachtsom")
    start = models.ForeignKey(
        'YearWeek',
        blank=True,
        null=True,
        default=this_year_week,
        related_name="starting_projects",
        verbose_name="startweek")
    end = models.ForeignKey(
        'YearWeek',
        blank=True,
        null=True,
        default=this_year_week,
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
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        verbose_name="groep",
        related_name="projects")
    is_accepted = models.BooleanField(
        verbose_name="goedgekeurd",
        help_text=("Project is goedgekeurd door PM en PL en kan qua team " +
                   "en budgetverdeling niet meer gewijzigd worden."),
        default=False)
    startup_meeting_done = models.BooleanField(
        verbose_name="startoverleg heeft plaatsgevonden",
        help_text=("Dit kan eenmalig door de projectleider aangevinkt worden"),
        default=False)
    is_subsidized = models.BooleanField(
        verbose_name="subsidieproject",
        help_text=("Dit project zit in een subsidietraject. " +
                   "Dit veld wordt gebruikt voor filtering."),
        default=False)
    remark = models.TextField(
        verbose_name="opmerkingen",
        blank=True,
        null=True)
    financial_remark = models.TextField(
        verbose_name="financiële opmerkingen",
        help_text="Bedoeld voor het office management",
        blank=True,
        null=True)
    cache_indicator = models.IntegerField(
        default=0,
        verbose_name="cache indicator")

    class Meta:
        verbose_name = "project"
        verbose_name_plural = "projecten"
        ordering = ('internal', '-code')

    def save(self, *args, **kwargs):
        self.cache_indicator += 1
        result = super(Project, self).save(*args, **kwargs)
        # We need to be saved before adding foreign keys to ourselves.
        if tls_request:
            # If not tls_request, we're in some automated import loop.
            for person in [self.project_manager, self.project_leader]:
                if person and person not in self.assigned_persons():
                    work_assignment = WorkAssignment(
                        assigned_to=person,
                        assigned_on=self,
                        hourly_tariff=person.standard_hourly_tariff())
                    work_assignment.save(save_assigned_on=False)
                    msg = "%s automatisch toegevoegd aan project" % person
                    messages.info(tls_request, msg)
        return result

    def __str__(self):
        return self.code

    def get_absolute_url(self):
        return reverse('trs.project', kwargs={'pk': self.pk})

    def cache_key(self, for_what):
        version = 5
        return 'project-%s-%s-%s-%s' % (self.id, self.cache_indicator,
                                        for_what, version)

    def as_widget(self):
        return mark_safe(render_to_string('trs/project-widget.html',
                                          {'project': self}))

    @cache_on_model
    def not_yet_started(self):
        if not self.start:
            return False
        return self.start.first_day > this_year_week().first_day

    @cache_on_model
    def already_ended(self):
        if not self.end:
            return False
        return self.end.first_day < this_year_week().first_day

    def assigned_persons(self):
        return Person.objects.filter(
            work_assignments__assigned_on=self).distinct()

    def hour_budget(self):
        return self.work_calculation()['budget']

    def overbooked(self):
        return self.work_calculation()['overbooked']

    def left_to_book(self):
        return self.work_calculation()['left_to_book']

    def turnover(self):
        return self.work_calculation()['turnover']

    def costs(self):
        return self.work_calculation()['costs']

    def reserved(self):
        return self.work_calculation()['reserved']

    def overbooked_percentage(self):
        if not self.overbooked():
            return 0
        if not self.hour_budget():  # Division by zero
            return 100
        return round(self.overbooked() / self.hour_budget() * 100)

    @cache_on_model
    def work_calculation(self):
        # The big calculation from which the rest derives.
        work_per_person = WorkAssignment.objects.filter(
            assigned_on=self).values(
                'assigned_to').annotate(
                    models.Sum('hours'),
                    models.Sum('hourly_tariff'))
        budget_per_person = {
            item['assigned_to']: round(item['hours__sum'] or 0)
            for item in work_per_person}
        hourly_tariff_per_person = {
            item['assigned_to']: round(item['hourly_tariff__sum'] or 0)
            for item in work_per_person}
        ids = budget_per_person.keys()

        booked_this_year_per_person = Booking.objects.filter(
            booked_on=self,
            booked_by__in=ids).values(
                'booked_by').annotate(
                    models.Sum('hours'))
        total_booked_per_person = {
            item['booked_by']: round(item['hours__sum'])
            for item in booked_this_year_per_person}

        budget_items = self.budget_items.all().values(
            'is_reservation').annotate(
                models.Sum('amount'))
        # Warning: 'costs' used to be the total of all budget items, now it
        # excludes the reservations.
        costs_per_kind = {item['is_reservation']: item['amount__sum'] or 0
                          for item in budget_items}
        reserved = -1 * costs_per_kind.get(True, 0)
        costs = -1 * costs_per_kind.get(False, 0)

        overbooked_per_person = {
            id: max(0, (total_booked_per_person.get(id, 0) -
                        budget_per_person[id]))
            for id in ids}
        well_booked_per_person = {
            id: (total_booked_per_person.get(id, 0) -
                 overbooked_per_person[id])
            for id in ids}
        left_to_book_per_person = {
            id: (budget_per_person[id] - well_booked_per_person[id])
            for id in ids}

        if self.contract_amount:
            tariff = {id: hourly_tariff_per_person[id]
                      for id in ids}
        else:
            # Don't count anything money-wise.
            tariff = {id: 0 for id in ids}
        turnover_per_person = {
            id: (well_booked_per_person[id] * tariff[id])
            for id in ids}
        left_to_turn_over_per_person = {
            id: (left_to_book_per_person[id] * tariff[id])
            for id in ids}

        return {'budget': sum(budget_per_person.values()),
                'overbooked': sum(overbooked_per_person.values()),
                'well_booked': sum(well_booked_per_person.values()),
                'left_to_book': sum(left_to_book_per_person.values()),
                'turnover': sum(turnover_per_person.values()),
                'left_to_turn_over': sum(
                    left_to_turn_over_per_person.values()),
                'costs': costs,
                'reserved': reserved}


class FinancialBase(models.Model):
    added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="toegevoegd op")
    added_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        #editable=False,
        verbose_name="toegevoegd door")
    # ^^^ The two above are copied from EventBase.

    class Meta:
        abstract = True
        ordering = ['project', 'added']

    def save(self, *args, **kwargs):
        # Partially copied form EventBase.
        if not self.added_by:
            if tls_request:
                # If tls_request doesn't exist we're running tests. Adding
                # this 'if' is handier than mocking it the whole time :-)
                self.added_by = tls_request.user
        self.project.save()
        # ^^^ Project is available on subclasses. This increments the cache
        # key.
        return super(FinancialBase, self).save(*args, **kwargs)


class Invoice(FinancialBase):
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
        ordering = ('date', 'number',)

    def __str__(self):
        return self.number

    def get_absolute_url(self):
        return reverse('trs.invoice.edit', kwargs={
            'pk': self.pk,
            'project_pk': self.project.pk})

    @property
    def amount_inclusive(self):
        return self.amount_exclusive + self.vat


class BudgetItem(FinancialBase):
    project = models.ForeignKey(
        Project,
        related_name="budget_items",
        verbose_name="project")
    description = models.CharField(
        verbose_name="omschrijving",
        blank=True,
        max_length=255)
    amount = models.DecimalField(
        max_digits=12,  # We don't mind a metric ton of hard cash.
        decimal_places=DECIMAL_PLACES,
        default=0,
        verbose_name="bedrag exclusief",
        help_text=("Opgepast: positieve bedragen verhogen ons budget, " +
                   "negatieve verlagen het. Het wordt dus niet automatisch " +
                   "afgetrokken."))
    is_reservation = models.BooleanField(
        verbose_name="reservering",
        help_text=("Bedrag dat nu apart wordt gezet om in de toekomst te " +
                   "gebruiken extra te verdelen uren + budget."),
        default=False)

    class Meta:
        verbose_name = "begrotingsitem"
        verbose_name_plural = "begrotingsitems"

    def __str__(self):
        return self.description

    def amount_as_costs(self):
        # The value should be inversed  when used as costs.
        return -1 * self.amount

    def get_absolute_url(self):
        return reverse('trs.budget_item.edit', kwargs={
            'pk': self.pk,
            'project_pk': self.project.pk})


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
    num_days_missing = models.IntegerField(
        verbose_name="aantal dagen dat mist",
        help_text="(Alleen relevant voor de eerste en laatste week v/h jaar)",
        default=0)

    class Meta:
        verbose_name = "jaar/week combinatie"
        verbose_name_plural = "jaar/week combinaties"
        ordering = ['year', 'week']

    def __str__(self):
        return "{}  (week {:02d})".format(self.first_day, self.week)

    def as_param(self):
        """Return string representation for in url parameters."""
        return "{}-{:02d}".format(self.year, self.week)

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
    minimum_hourly_tariff = models.DecimalField(
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        blank=True,
        null=True,
        verbose_name="minimum uurtarief")

    person = models.ForeignKey(
        Person,
        blank=True,
        null=True,
        verbose_name="persoon",
        help_text="persoon waar de verandering voor is",
        related_name="person_changes")

    def save(self, *args, **kwargs):
        self.person.cache_indicator_person_change += 1  # Specially for us.
        self.person.save()  # Increments cache indicator.
        return super(PersonChange, self).save(*args, **kwargs)

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

    def save(self, *args, **kwargs):
        self.booked_by.save()  # Increments cache indicator.
        self.booked_on.save()  # Increments cache indicator.
        return super(Booking, self).save(*args, **kwargs)


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

    def save(self, save_assigned_on=True, *args, **kwargs):
        self.assigned_to.save()  # Increments cache indicator.
        if save_assigned_on:
            self.assigned_on.save()  # Increments cache indicator.
        return super(WorkAssignment, self).save(*args, **kwargs)
