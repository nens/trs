# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import trs.models
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('added', models.DateTimeField(auto_now_add=True, verbose_name='toegevoegd op')),
                ('hours', models.DecimalField(blank=True, decimal_places=2, verbose_name='uren', max_digits=8, null=True)),
                ('added_by', models.ForeignKey(verbose_name='toegevoegd door', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'boeking',
                'verbose_name_plural': 'boekingen',
            },
        ),
        migrations.CreateModel(
            name='BudgetItem',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('added', models.DateTimeField(auto_now_add=True, verbose_name='toegevoegd op')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='omschrijving')),
                ('amount', models.DecimalField(help_text='Dit zijn kosten, dus een positief getal wordt van het projectbudget afgetrokken. (Dit is in sept 2014 veranderd!)', decimal_places=2, verbose_name='bedrag exclusief', max_digits=12, default=0)),
                ('added_by', models.ForeignKey(verbose_name='toegevoegd door', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'projectkostenpost',
                'verbose_name_plural': 'projectkostenposten',
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='naam')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='omschrijving')),
                ('target', models.DecimalField(decimal_places=2, verbose_name='omzetdoelstelling', max_digits=12, default=0)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'groep',
                'verbose_name_plural': 'groepen',
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('added', models.DateTimeField(auto_now_add=True, verbose_name='toegevoegd op')),
                ('date', models.DateField(help_text='Formaat: 25-12-1972, dd-mm-jjjj', verbose_name='factuurdatum')),
                ('number', models.CharField(max_length=255, verbose_name='factuurnummer')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='omschrijving')),
                ('amount_exclusive', models.DecimalField(decimal_places=2, verbose_name='bedrag exclusief', max_digits=12, default=0)),
                ('vat', models.DecimalField(decimal_places=2, verbose_name='btw', max_digits=12, default=0)),
                ('payed', models.DateField(blank=True, help_text='Formaat: 25-12-1972, dd-mm-jjjj', verbose_name='betaald op', null=True)),
                ('added_by', models.ForeignKey(verbose_name='toegevoegd door', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('date', 'number'),
                'verbose_name': 'factuur',
                'verbose_name_plural': 'facturen',
            },
        ),
        migrations.CreateModel(
            name='Payable',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('added', models.DateTimeField(auto_now_add=True, verbose_name='toegevoegd op')),
                ('date', models.DateField(help_text='Formaat: 25-12-1972, dd-mm-jjjj', verbose_name='factuurdatum')),
                ('number', models.CharField(max_length=255, verbose_name='factuurnummer')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='omschrijving')),
                ('amount', models.DecimalField(help_text='Dit zijn kosten, dus een positief getal wordt van het projectbudget afgetrokken. Bedrag is ex btw.', decimal_places=2, verbose_name='bedrag exclusief', max_digits=12, default=0)),
                ('payed', models.DateField(blank=True, help_text='Formaat: 25-12-1972, dd-mm-jjjj', verbose_name='overgemaakt op', null=True)),
                ('added_by', models.ForeignKey(verbose_name='toegevoegd door', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('date', 'number'),
                'verbose_name': 'kosten derden',
                'verbose_name_plural': 'kosten derden',
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='naam')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='omschrijving')),
                ('is_office_management', models.BooleanField(help_text='Office management can edit and add everything', verbose_name='office management', default=False)),
                ('is_management', models.BooleanField(help_text="Management can see everything, but doesn't get extra edit rights", verbose_name='management', default=False)),
                ('archived', models.BooleanField(verbose_name='gearchiveerd', default=False)),
                ('cache_indicator', models.IntegerField(verbose_name='cache indicator', default=0)),
                ('cache_indicator_person_change', models.IntegerField(verbose_name='cache indicator voor PersonChange veranderingen', default=0)),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='laatst gewijzigd')),
                ('group', models.ForeignKey(verbose_name='groep', blank=True, to='trs.Group', null=True, related_name='persons')),
                ('user', models.ForeignKey(help_text='De interne (django) gebruiker die deze persoon is. Dit wordt normaliter automatisch gekoppeld op basis vande loginnaam zodra de gebruiker voor de eerste keer inlogt.', unique=True, verbose_name='gebruiker', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['archived', 'name'],
                'verbose_name': 'persoon',
                'verbose_name_plural': 'personen',
            },
        ),
        migrations.CreateModel(
            name='PersonChange',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('added', models.DateTimeField(auto_now_add=True, verbose_name='toegevoegd op')),
                ('hours_per_week', models.DecimalField(blank=True, decimal_places=2, verbose_name='uren per week', max_digits=8, null=True)),
                ('target', models.DecimalField(blank=True, decimal_places=2, verbose_name='target', max_digits=8, null=True)),
                ('standard_hourly_tariff', models.DecimalField(blank=True, decimal_places=2, verbose_name='standaard uurtarief', max_digits=8, null=True)),
                ('minimum_hourly_tariff', models.DecimalField(blank=True, decimal_places=2, verbose_name='minimum uurtarief', max_digits=8, null=True)),
                ('added_by', models.ForeignKey(verbose_name='toegevoegd door', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('person', models.ForeignKey(help_text='persoon waar de verandering voor is', verbose_name='persoon', blank=True, to='trs.Person', null=True, related_name='person_changes')),
            ],
            options={
                'verbose_name': 'verandering aan persoon',
                'verbose_name_plural': 'veranderingen aan personen',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('code', models.CharField(unique=True, max_length=255, verbose_name='projectcode')),
                ('code_for_sorting', models.CharField(blank=True, max_length=255, null=True, editable=False)),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='omschrijving')),
                ('added', models.DateTimeField(auto_now_add=True, verbose_name='toegevoegd op')),
                ('internal', models.BooleanField(verbose_name='intern project', default=False)),
                ('hidden', models.BooleanField(help_text="Zet dit standaard aan voor interne projecten, tenzij het een 'echt' project is waar uren voor staan. Afgeschermde projecten kan je andermans gegevens niet van zien. Goed voor ziekte enzo.", verbose_name='afgeschermd project', default=False)),
                ('hourless', models.BooleanField(help_text='Uren van dit project tellen niet mee voor de intern/extern verhouding en binnen/buiten budget. Gebruik dit voor verlof en zwangerschapsverlof.', verbose_name='tel uren niet mee', default=False)),
                ('archived', models.BooleanField(verbose_name='gearchiveerd', default=False)),
                ('principal', models.CharField(blank=True, max_length=255, verbose_name='opdrachtgever')),
                ('contract_amount', models.DecimalField(decimal_places=2, verbose_name='opdrachtsom', max_digits=12, default=0)),
                ('bid_send_date', models.DateField(blank=True, help_text='Formaat: 25-12-1972, dd-mm-jjjj', verbose_name='offerte verzonden', null=True)),
                ('confirmation_date', models.DateField(blank=True, help_text='Formaat: 25-12-1972, dd-mm-jjjj', verbose_name='opdrachtbevestiging binnen', null=True)),
                ('reservation', models.DecimalField(decimal_places=2, verbose_name='reservering voor personele kosten', max_digits=12, default=0)),
                ('wbso_percentage', models.IntegerField(blank=True, help_text='Percentage dat meetelt voor de WBSO (0-100)', verbose_name='WBSO percentage', null=True)),
                ('is_accepted', models.BooleanField(help_text='Project is goedgekeurd door PM en PL en zou qua team en budgetverdeling niet meer gewijzigd moeten worden.', verbose_name='goedgekeurd', default=False)),
                ('startup_meeting_done', models.BooleanField(verbose_name='startoverleg heeft plaatsgevonden', default=False)),
                ('is_subsidized', models.BooleanField(help_text='Dit project zit in een subsidietraject. Dit veld wordt gebruikt voor filtering.', verbose_name='subsidieproject', default=False)),
                ('remark', models.TextField(blank=True, verbose_name='opmerkingen', null=True)),
                ('financial_remark', models.TextField(blank=True, help_text='Bedoeld voor het office management', verbose_name='financiële opmerkingen', null=True)),
                ('rating_projectteam', models.IntegerField(blank=True, verbose_name='rapportcijfer v/h projectteam', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)], null=True)),
                ('rating_projectteam_reason', models.TextField(blank=True, verbose_name='Evt. onderbouwing rapportcijfer v/h projectteam', null=True)),
                ('rating_customer', models.IntegerField(blank=True, verbose_name='rapportcijfer v/d klant', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)], null=True)),
                ('rating_customer_reason', models.TextField(blank=True, verbose_name='Evt. onderbouwing rapportcijfer v/d klant', null=True)),
                ('cache_indicator', models.IntegerField(verbose_name='cache indicator', default=0)),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='laatst gewijzigd')),
            ],
            options={
                'ordering': ('internal', '-code_for_sorting'),
                'verbose_name': 'project',
                'verbose_name_plural': 'projecten',
            },
        ),
        migrations.CreateModel(
            name='WbsoProject',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('number', models.IntegerField(help_text='Gebruikt voor sortering', max_length=255, verbose_name='Nummer')),
                ('title', models.CharField(unique=True, max_length=255, verbose_name='titel')),
                ('start_date', models.DateField(help_text='Formaat: 25-12-1972, dd-mm-jjjj', verbose_name='startdatum')),
                ('end_date', models.DateField(help_text='Formaat: 25-12-1972, dd-mm-jjjj', verbose_name='einddatum')),
            ],
            options={
                'ordering': ['number'],
                'verbose_name': 'WBSO project',
                'verbose_name_plural': 'WBSO projecten',
            },
        ),
        migrations.CreateModel(
            name='WorkAssignment',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('added', models.DateTimeField(auto_now_add=True, verbose_name='toegevoegd op')),
                ('hours', models.DecimalField(blank=True, decimal_places=2, verbose_name='uren', max_digits=8, null=True)),
                ('hourly_tariff', models.DecimalField(blank=True, decimal_places=2, verbose_name='uurtarief', max_digits=8, null=True)),
                ('added_by', models.ForeignKey(verbose_name='toegevoegd door', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('assigned_on', models.ForeignKey(verbose_name='toegekend voor', blank=True, to='trs.Project', null=True, related_name='work_assignments')),
                ('assigned_to', models.ForeignKey(verbose_name='toegekend aan', blank=True, to='trs.Person', null=True, related_name='work_assignments')),
            ],
            options={
                'verbose_name': 'toekenning van werk',
                'verbose_name_plural': 'toekenningen van werk',
            },
        ),
        migrations.CreateModel(
            name='YearWeek',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('year', models.IntegerField(verbose_name='jaar')),
                ('week', models.IntegerField(verbose_name='weeknummer')),
                ('first_day', models.DateField(db_index=True, verbose_name='eerste maandag van de week')),
                ('num_days_missing', models.IntegerField(help_text='(Alleen relevant voor de eerste en laatste week v/h jaar)', verbose_name='aantal dagen dat mist', default=0)),
            ],
            options={
                'ordering': ['year', 'week'],
                'verbose_name': 'jaar/week combinatie',
                'verbose_name_plural': 'jaar/week combinaties',
            },
        ),
        migrations.AddField(
            model_name='workassignment',
            name='year_week',
            field=models.ForeignKey(help_text='Ingangsdatum van de wijziging (of datum van de boeking)', verbose_name='jaar en week', blank=True, to='trs.YearWeek', null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='end',
            field=models.ForeignKey(default=trs.models.this_year_week_pk, blank=True, to='trs.YearWeek', related_name='ending_projects', null=True, verbose_name='laatste week'),
        ),
        migrations.AddField(
            model_name='project',
            name='group',
            field=models.ForeignKey(verbose_name='groep', blank=True, to='trs.Group', null=True, related_name='projects'),
        ),
        migrations.AddField(
            model_name='project',
            name='project_leader',
            field=models.ForeignKey(verbose_name='projectleider', blank=True, to='trs.Person', null=True, related_name='projects_i_lead'),
        ),
        migrations.AddField(
            model_name='project',
            name='project_manager',
            field=models.ForeignKey(verbose_name='projectmanager', blank=True, to='trs.Person', null=True, related_name='projects_i_manage'),
        ),
        migrations.AddField(
            model_name='project',
            name='start',
            field=models.ForeignKey(default=trs.models.this_year_week_pk, blank=True, to='trs.YearWeek', related_name='starting_projects', null=True, verbose_name='startweek'),
        ),
        migrations.AddField(
            model_name='project',
            name='wbso_project',
            field=models.ForeignKey(verbose_name='WBSO project', blank=True, to='trs.WbsoProject', null=True, related_name='projects'),
        ),
        migrations.AddField(
            model_name='personchange',
            name='year_week',
            field=models.ForeignKey(help_text='Ingangsdatum van de wijziging (of datum van de boeking)', verbose_name='jaar en week', blank=True, to='trs.YearWeek', null=True),
        ),
        migrations.AddField(
            model_name='payable',
            name='project',
            field=models.ForeignKey(verbose_name='project', to='trs.Project', related_name='payables'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='project',
            field=models.ForeignKey(verbose_name='project', to='trs.Project', related_name='invoices'),
        ),
        migrations.AddField(
            model_name='budgetitem',
            name='project',
            field=models.ForeignKey(verbose_name='project', to='trs.Project', related_name='budget_items'),
        ),
        migrations.AddField(
            model_name='budgetitem',
            name='to_project',
            field=models.ForeignKey(help_text='optioneel: project waarnaar het bedrag wordt overgemaakt', verbose_name='overboeken naar ander project', blank=True, to='trs.Project', null=True, related_name='budget_transfers'),
        ),
        migrations.AddField(
            model_name='booking',
            name='booked_by',
            field=models.ForeignKey(verbose_name='geboekt door', blank=True, to='trs.Person', null=True, related_name='bookings'),
        ),
        migrations.AddField(
            model_name='booking',
            name='booked_on',
            field=models.ForeignKey(verbose_name='geboekt op', blank=True, to='trs.Project', null=True, related_name='bookings'),
        ),
        migrations.AddField(
            model_name='booking',
            name='year_week',
            field=models.ForeignKey(help_text='Ingangsdatum van de wijziging (of datum van de boeking)', verbose_name='jaar en week', blank=True, to='trs.YearWeek', null=True),
        ),
    ]
