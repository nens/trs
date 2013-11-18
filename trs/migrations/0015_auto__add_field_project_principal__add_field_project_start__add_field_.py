# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Project.principal'
        db.add_column('trs_project', 'principal',
                      self.gf('django.db.models.fields.CharField')(blank=True, max_length=255, default=''),
                      keep_default=False)

        # Adding field 'Project.start'
        db.add_column('trs_project', 'start',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['trs.YearWeek'], related_name='starting_projects', null=True),
                      keep_default=False)

        # Adding field 'Project.end'
        db.add_column('trs_project', 'end',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['trs.YearWeek'], related_name='ending_projects', null=True),
                      keep_default=False)

        # Adding field 'Project.project_leader'
        db.add_column('trs_project', 'project_leader',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['trs.Person'], related_name='projects_i_lead', null=True),
                      keep_default=False)

        # Adding field 'Project.project_manager'
        db.add_column('trs_project', 'project_manager',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['trs.Person'], related_name='projects_i_manage', null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Project.principal'
        db.delete_column('trs_project', 'principal')

        # Deleting field 'Project.start'
        db.delete_column('trs_project', 'start_id')

        # Deleting field 'Project.end'
        db.delete_column('trs_project', 'end_id')

        # Deleting field 'Project.project_leader'
        db.delete_column('trs_project', 'project_leader_id')

        # Deleting field 'Project.project_manager'
        db.delete_column('trs_project', 'project_manager_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'", 'object_name': 'ContentType'},
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
            'hours': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'null': 'True'})
        },
        'trs.budgetassignment': {
            'Meta': {'object_name': 'BudgetAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Project']", 'related_name': "'budget_assignments'", 'null': 'True'}),
            'budget': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '12', 'decimal_places': '2', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'null': 'True'})
        },
        'trs.person': {
            'Meta': {'ordering': "['name']", 'object_name': 'Person'},
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'})
        },
        'trs.personchange': {
            'Meta': {'object_name': 'PersonChange'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'hours_per_week': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Person']", 'related_name': "'person_changes'", 'null': 'True'}),
            'target': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'null': 'True'})
        },
        'trs.project': {
            'Meta': {'ordering': "['code']", 'object_name': 'Project'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'end': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'related_name': "'ending_projects'", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'principal': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'project_leader': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Person']", 'related_name': "'projects_i_lead'", 'null': 'True'}),
            'project_manager': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Person']", 'related_name': "'projects_i_manage'", 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'start': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'related_name': "'starting_projects'", 'null': 'True'})
        },
        'trs.workassignment': {
            'Meta': {'object_name': 'WorkAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'assigned_on': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Project']", 'related_name': "'work_assignments'", 'null': 'True'}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.Person']", 'related_name': "'work_assignments'", 'null': 'True'}),
            'hourly_tariff': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['trs.YearWeek']", 'null': 'True'})
        },
        'trs.yearweek': {
            'Meta': {'ordering': "['year', 'week']", 'object_name': 'YearWeek'},
            'first_day': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'week': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['trs']