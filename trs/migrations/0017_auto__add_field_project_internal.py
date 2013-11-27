# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Project.internal'
        db.add_column('trs_project', 'internal',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Project.internal'
        db.delete_column('trs_project', 'internal')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Permission']", 'blank': 'True'})
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'", 'ordering': "('name',)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'trs.booking': {
            'Meta': {'object_name': 'Booking'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'booked_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Person']", 'related_name': "'bookings'", 'null': 'True', 'blank': 'True'}),
            'booked_on': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'related_name': "'bookings'", 'null': 'True', 'blank': 'True'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'max_digits': '8', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'null': 'True', 'blank': 'True'})
        },
        'trs.budgetassignment': {
            'Meta': {'object_name': 'BudgetAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'related_name': "'budget_assignments'", 'null': 'True', 'blank': 'True'}),
            'budget': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'max_digits': '12', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'null': 'True', 'blank': 'True'})
        },
        'trs.person': {
            'Meta': {'object_name': 'Person', 'ordering': "['name']"},
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'trs.personchange': {
            'Meta': {'object_name': 'PersonChange'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'hours_per_week': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'max_digits': '8', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Person']", 'related_name': "'person_changes'", 'null': 'True', 'blank': 'True'}),
            'target': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'max_digits': '8', 'null': 'True', 'blank': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'null': 'True', 'blank': 'True'})
        },
        'trs.project': {
            'Meta': {'object_name': 'Project', 'ordering': "['code']"},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'end': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'related_name': "'ending_projects'", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'principal': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'project_leader': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Person']", 'related_name': "'projects_i_lead'", 'null': 'True', 'blank': 'True'}),
            'project_manager': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Person']", 'related_name': "'projects_i_manage'", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'start': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'related_name': "'starting_projects'", 'null': 'True', 'blank': 'True'})
        },
        'trs.workassignment': {
            'Meta': {'object_name': 'WorkAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'assigned_on': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'related_name': "'work_assignments'", 'null': 'True', 'blank': 'True'}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Person']", 'related_name': "'work_assignments'", 'null': 'True', 'blank': 'True'}),
            'hourly_tariff': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'max_digits': '8', 'null': 'True', 'blank': 'True'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'max_digits': '8', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'null': 'True', 'blank': 'True'})
        },
        'trs.yearweek': {
            'Meta': {'object_name': 'YearWeek', 'ordering': "['year', 'week']"},
            'first_day': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'week': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['trs']