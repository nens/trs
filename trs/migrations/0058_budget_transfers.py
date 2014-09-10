# -*- coding: utf-8 -*-
import datetime
import re
from collections import defaultdict

from south.db import db
from south.v2 import DataMigration
from django.db import models


#PROJECT_REGEX = r'[a-z][0-9]{4}

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName".
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        transferred_to = defaultdict(list)
        received_by = defaultdict(list)
        for budget_item in orm.BudgetItem.objects.all():
            description = budget_item.description.lower().strip()
            parts = description.split(' ')
            if len(parts) != 2:
                continue
            other_project = parts[1]
            if '.' not in other_project:
                continue
            ourselves = budget_item.project.code.lower()
            if description.startswith('van'):
                received_by[ourselves].append([other_project, -1 * budget_item.amount, budget_item])
            if description.startswith('naar'):
                transferred_to[other_project].append([ourselves, budget_item.amount, budget_item])

        to_delete = set()
        for target_project_code in transferred_to.keys():
            for (source_project_code1,
                 source_amount1,
                 budget_item1) in transferred_to[target_project_code]:
                for (source_project_code2,
                     source_amount2,
                     budget_item2) in received_by[target_project_code]:
                    if source_project_code1 == source_project_code2:
                        if source_amount1 == source_amount2:
                            print("Match: %s from '%s' to '%s'" % (
                                budget_item1.amount,
                                budget_item1.project.code,
                                budget_item2.project.code))
                            budget_item1.description = "overboeking"
                            budget_item1.to_project = budget_item2.project
                            budget_item1.save()
                            to_delete.add(budget_item2.id)
                        else:
                            print("Amounts don't match between '%s' and '%s': %s and %s" % (
                                budget_item1.description,
                                budget_item2.description,
                                source_amount1, source_amount2))

        orm.BudgetItem.objects.filter(id__in=list(to_delete)).delete()

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'symmetrical': 'False', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'Permission', 'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'user_set'", 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'user_set'", 'symmetrical': 'False', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'ordering': "('name',)", 'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'trs.booking': {
            'Meta': {'object_name': 'Booking'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['auth.User']"}),
            'booked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'bookings'", 'to': "orm['trs.Person']"}),
            'booked_on': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'bookings'", 'to': "orm['trs.Project']"}),
            'hours': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'max_digits': '8', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['trs.YearWeek']"})
        },
        'trs.budgetitem': {
            'Meta': {'object_name': 'BudgetItem'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['auth.User']"}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2', 'default': '0'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_third_party_cost': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'budget_items'", 'to': "orm['trs.Project']"}),
            'to_project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'budget_transfers'", 'to': "orm['trs.Project']"})
        },
        'trs.group': {
            'Meta': {'ordering': "['name']", 'object_name': 'Group'},
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'trs.invoice': {
            'Meta': {'ordering': "('date', 'number')", 'object_name': 'Invoice'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['auth.User']"}),
            'amount_exclusive': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2', 'default': '0'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'payed': ('django.db.models.fields.DateField', [], {'blank': 'True', 'null': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invoices'", 'to': "orm['trs.Project']"}),
            'vat': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2', 'default': '0'})
        },
        'trs.person': {
            'Meta': {'ordering': "['archived', 'name']", 'object_name': 'Person'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cache_indicator': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cache_indicator_person_change': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'persons'", 'to': "orm['trs.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_office_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'unique': 'True', 'blank': 'True', 'null': 'True', 'to': "orm['auth.User']"})
        },
        'trs.personchange': {
            'Meta': {'object_name': 'PersonChange'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['auth.User']"}),
            'hours_per_week': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'max_digits': '8', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'minimum_hourly_tariff': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'max_digits': '8', 'decimal_places': '2'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'person_changes'", 'to': "orm['trs.Person']"}),
            'standard_hourly_tariff': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'max_digits': '8', 'decimal_places': '2'}),
            'target': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'max_digits': '8', 'decimal_places': '2'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['trs.YearWeek']"})
        },
        'trs.project': {
            'Meta': {'ordering': "('internal', '-code_for_sorting')", 'object_name': 'Project'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cache_indicator': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'code_for_sorting': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '255'}),
            'contract_amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2', 'default': '0'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'ending_projects'", 'to': "orm['trs.YearWeek']"}),
            'financial_remark': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'projects'", 'to': "orm['trs.Group']"}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hourless': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_subsidized': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'principal': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'project_leader': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'projects_i_lead'", 'to': "orm['trs.Person']"}),
            'project_manager': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'projects_i_manage'", 'to': "orm['trs.Person']"}),
            'remark': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'reservation': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2', 'default': '0'}),
            'start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'starting_projects'", 'to': "orm['trs.YearWeek']"}),
            'startup_meeting_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'trs.workassignment': {
            'Meta': {'object_name': 'WorkAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['auth.User']"}),
            'assigned_on': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'work_assignments'", 'to': "orm['trs.Project']"}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'related_name': "'work_assignments'", 'to': "orm['trs.Person']"}),
            'hourly_tariff': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'max_digits': '8', 'decimal_places': '2'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'max_digits': '8', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['trs.YearWeek']"})
        },
        'trs.yearweek': {
            'Meta': {'ordering': "['year', 'week']", 'object_name': 'YearWeek'},
            'first_day': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_days_missing': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'week': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['trs']
    symmetrical = True
