# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'BudgetItem.is_third_party_cost'
        db.delete_column('trs_budgetitem', 'is_third_party_cost')


    def backwards(self, orm):
        # Adding field 'BudgetItem.is_third_party_cost'
        db.add_column('trs_budgetitem', 'is_third_party_cost',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission', 'ordering': "('content_type__app_label', 'content_type__model', 'codename')"},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Group']", 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'ordering': "('name',)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'trs.booking': {
            'Meta': {'object_name': 'Booking'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'booked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Person']", 'related_name': "'bookings'", 'null': 'True'}),
            'booked_on': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Project']", 'related_name': "'bookings'", 'null': 'True'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'null': 'True', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'null': 'True'})
        },
        'trs.budgetitem': {
            'Meta': {'object_name': 'BudgetItem'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'related_name': "'budget_items'"}),
            'to_project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Project']", 'related_name': "'budget_transfers'", 'null': 'True'})
        },
        'trs.group': {
            'Meta': {'object_name': 'Group', 'ordering': "['name']"},
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'trs.invoice': {
            'Meta': {'object_name': 'Invoice', 'ordering': "('date', 'number')"},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'amount_exclusive': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'payed': ('django.db.models.fields.DateField', [], {'blank': 'True', 'null': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'related_name': "'invoices'"}),
            'vat': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'})
        },
        'trs.person': {
            'Meta': {'object_name': 'Person', 'ordering': "['archived', 'name']"},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cache_indicator': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cache_indicator_person_change': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Group']", 'related_name': "'persons'", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_office_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'unique': 'True', 'to': "orm['auth.User']", 'null': 'True'})
        },
        'trs.personchange': {
            'Meta': {'object_name': 'PersonChange'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'hours_per_week': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'null': 'True', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'minimum_hourly_tariff': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'null': 'True', 'decimal_places': '2'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Person']", 'related_name': "'person_changes'", 'null': 'True'}),
            'standard_hourly_tariff': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'null': 'True', 'decimal_places': '2'}),
            'target': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'null': 'True', 'decimal_places': '2'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'null': 'True'})
        },
        'trs.project': {
            'Meta': {'object_name': 'Project', 'ordering': "('internal', '-code_for_sorting')"},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cache_indicator': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'code_for_sorting': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '255'}),
            'contract_amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'related_name': "'ending_projects'", 'null': 'True'}),
            'financial_remark': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Group']", 'related_name': "'projects'", 'null': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hourless': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_subsidized': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'principal': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'project_leader': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Person']", 'related_name': "'projects_i_lead'", 'null': 'True'}),
            'project_manager': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Person']", 'related_name': "'projects_i_manage'", 'null': 'True'}),
            'remark': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'reservation': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2'}),
            'start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'related_name': "'starting_projects'", 'null': 'True'}),
            'startup_meeting_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'trs.workassignment': {
            'Meta': {'object_name': 'WorkAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'assigned_on': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Project']", 'related_name': "'work_assignments'", 'null': 'True'}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Person']", 'related_name': "'work_assignments'", 'null': 'True'}),
            'hourly_tariff': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'null': 'True', 'decimal_places': '2'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'null': 'True', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'null': 'True'})
        },
        'trs.yearweek': {
            'Meta': {'object_name': 'YearWeek', 'ordering': "['year', 'week']"},
            'first_day': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_days_missing': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'week': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['trs']