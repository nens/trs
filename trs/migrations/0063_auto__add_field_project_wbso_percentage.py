# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Project.wbso_percentage'
        db.add_column('trs_project', 'wbso_percentage',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Project.wbso_percentage'
        db.delete_column('trs_project', 'wbso_percentage')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Group']", 'related_name': "'user_set'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']", 'related_name': "'user_set'"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'trs.booking': {
            'Meta': {'object_name': 'Booking'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['auth.User']", 'blank': 'True'}),
            'booked_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Person']", 'blank': 'True', 'related_name': "'bookings'"}),
            'booked_on': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Project']", 'blank': 'True', 'related_name': "'bookings'"}),
            'hours': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'blank': 'True', 'decimal_places': '2', 'max_digits': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.YearWeek']", 'blank': 'True'})
        },
        'trs.budgetitem': {
            'Meta': {'object_name': 'BudgetItem'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['auth.User']", 'blank': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'decimal_places': '2', 'max_digits': '12'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'related_name': "'budget_items'"}),
            'to_project': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Project']", 'blank': 'True', 'related_name': "'budget_transfers'"})
        },
        'trs.group': {
            'Meta': {'object_name': 'Group', 'ordering': "['name']"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'trs.invoice': {
            'Meta': {'object_name': 'Invoice', 'ordering': "('date', 'number')"},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['auth.User']", 'blank': 'True'}),
            'amount_exclusive': ('django.db.models.fields.DecimalField', [], {'default': '0', 'decimal_places': '2', 'max_digits': '12'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'payed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'related_name': "'invoices'"}),
            'vat': ('django.db.models.fields.DecimalField', [], {'default': '0', 'decimal_places': '2', 'max_digits': '12'})
        },
        'trs.person': {
            'Meta': {'object_name': 'Person', 'ordering': "['archived', 'name']"},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cache_indicator': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cache_indicator_person_change': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Group']", 'blank': 'True', 'related_name': "'persons'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_office_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'unique': 'True', 'to': "orm['auth.User']", 'blank': 'True'})
        },
        'trs.personchange': {
            'Meta': {'object_name': 'PersonChange'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['auth.User']", 'blank': 'True'}),
            'hours_per_week': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'blank': 'True', 'decimal_places': '2', 'max_digits': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'minimum_hourly_tariff': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'blank': 'True', 'decimal_places': '2', 'max_digits': '8'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Person']", 'blank': 'True', 'related_name': "'person_changes'"}),
            'standard_hourly_tariff': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'blank': 'True', 'decimal_places': '2', 'max_digits': '8'}),
            'target': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'blank': 'True', 'decimal_places': '2', 'max_digits': '8'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.YearWeek']", 'blank': 'True'})
        },
        'trs.project': {
            'Meta': {'object_name': 'Project', 'ordering': "('internal', '-code_for_sorting')"},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bid_send_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'cache_indicator': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'code_for_sorting': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '255', 'blank': 'True'}),
            'confirmation_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'contract_amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'decimal_places': '2', 'max_digits': '12'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'end': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.YearWeek']", 'blank': 'True', 'related_name': "'ending_projects'"}),
            'financial_remark': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Group']", 'blank': 'True', 'related_name': "'projects'"}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hourless': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_subsidized': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'principal': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'project_leader': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Person']", 'blank': 'True', 'related_name': "'projects_i_lead'"}),
            'project_manager': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Person']", 'blank': 'True', 'related_name': "'projects_i_manage'"}),
            'remark': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'reservation': ('django.db.models.fields.DecimalField', [], {'default': '0', 'decimal_places': '2', 'max_digits': '12'}),
            'start': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.YearWeek']", 'blank': 'True', 'related_name': "'starting_projects'"}),
            'startup_meeting_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wbso_percentage': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wbso_project': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.WbsoProject']", 'blank': 'True', 'related_name': "'wbso_projects'"})
        },
        'trs.wbsoproject': {
            'Meta': {'object_name': 'WbsoProject', 'ordering': "['number']"},
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'max_length': '255'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'trs.workassignment': {
            'Meta': {'object_name': 'WorkAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['auth.User']", 'blank': 'True'}),
            'assigned_on': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Project']", 'blank': 'True', 'related_name': "'work_assignments'"}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.Person']", 'blank': 'True', 'related_name': "'work_assignments'"}),
            'hourly_tariff': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'blank': 'True', 'decimal_places': '2', 'max_digits': '8'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'blank': 'True', 'decimal_places': '2', 'max_digits': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['trs.YearWeek']", 'blank': 'True'})
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