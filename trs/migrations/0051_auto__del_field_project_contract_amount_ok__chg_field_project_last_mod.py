# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Project.contract_amount_ok'
        db.delete_column('trs_project', 'contract_amount_ok')


        # Changing field 'Project.last_modified'
        db.alter_column('trs_project', 'last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'Person.last_modified'
        db.alter_column('trs_person', 'last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

    def backwards(self, orm):
        # Adding field 'Project.contract_amount_ok'
        db.add_column('trs_project', 'contract_amount_ok',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


        # Changing field 'Project.last_modified'
        db.alter_column('trs_project', 'last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Person.last_modified'
        db.alter_column('trs_person', 'last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Permission']", 'blank': 'True'})
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
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'trs.booking': {
            'Meta': {'object_name': 'Booking'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'booked_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bookings'", 'to': "orm['trs.Person']", 'null': 'True', 'blank': 'True'}),
            'booked_on': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bookings'", 'to': "orm['trs.Project']", 'null': 'True', 'blank': 'True'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'null': 'True', 'blank': 'True'})
        },
        'trs.budgetitem': {
            'Meta': {'object_name': 'BudgetItem'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'default': '0', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_reservation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'budget_items'", 'to': "orm['trs.Project']"})
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
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'amount_exclusive': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'default': '0', 'decimal_places': '2'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'payed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invoices'", 'to': "orm['trs.Project']"}),
            'vat': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'default': '0', 'decimal_places': '2'})
        },
        'trs.person': {
            'Meta': {'object_name': 'Person', 'ordering': "['archived', 'name']"},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cache_indicator': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cache_indicator_person_change': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'persons'", 'to': "orm['trs.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_office_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'unique': 'True', 'blank': 'True'})
        },
        'trs.personchange': {
            'Meta': {'object_name': 'PersonChange'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'hours_per_week': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'minimum_hourly_tariff': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2', 'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'person_changes'", 'to': "orm['trs.Person']", 'null': 'True', 'blank': 'True'}),
            'standard_hourly_tariff': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2', 'null': 'True', 'blank': 'True'}),
            'target': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2', 'null': 'True', 'blank': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'null': 'True', 'blank': 'True'})
        },
        'trs.project': {
            'Meta': {'object_name': 'Project', 'ordering': "('internal', '-code_for_sorting')"},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cache_indicator': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True'}),
            'code_for_sorting': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'contract_amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'default': '0', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'end': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ending_projects'", 'to': "orm['trs.YearWeek']", 'null': 'True', 'blank': 'True'}),
            'financial_remark': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projects'", 'to': "orm['trs.Group']", 'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hourless': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_subsidized': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'principal': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'project_leader': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projects_i_lead'", 'to': "orm['trs.Person']", 'null': 'True', 'blank': 'True'}),
            'project_manager': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projects_i_manage'", 'to': "orm['trs.Person']", 'null': 'True', 'blank': 'True'}),
            'remark': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'starting_projects'", 'to': "orm['trs.YearWeek']", 'null': 'True', 'blank': 'True'}),
            'startup_meeting_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'trs.workassignment': {
            'Meta': {'object_name': 'WorkAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'assigned_on': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'work_assignments'", 'to': "orm['trs.Project']", 'null': 'True', 'blank': 'True'}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'work_assignments'", 'to': "orm['trs.Person']", 'null': 'True', 'blank': 'True'}),
            'hourly_tariff': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2', 'null': 'True', 'blank': 'True'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'null': 'True', 'blank': 'True'})
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