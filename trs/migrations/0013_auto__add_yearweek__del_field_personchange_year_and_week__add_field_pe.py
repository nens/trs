# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'YearWeek'
        db.create_table('trs_yearweek', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('year', self.gf('django.db.models.fields.IntegerField')()),
            ('week', self.gf('django.db.models.fields.IntegerField')()),
            ('first_day', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('trs', ['YearWeek'])

        # Deleting field 'PersonChange.year_and_week'
        db.delete_column('trs_personchange', 'year_and_week')

        # Adding field 'PersonChange.year_week'
        db.add_column('trs_personchange', 'year_week',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trs.YearWeek'], blank=True, null=True),
                      keep_default=False)

        # Deleting field 'WorkAssignment.year_and_week'
        db.delete_column('trs_workassignment', 'year_and_week')

        # Adding field 'WorkAssignment.year_week'
        db.add_column('trs_workassignment', 'year_week',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trs.YearWeek'], blank=True, null=True),
                      keep_default=False)

        # Deleting field 'Booking.year_and_week'
        db.delete_column('trs_booking', 'year_and_week')

        # Adding field 'Booking.year_week'
        db.add_column('trs_booking', 'year_week',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trs.YearWeek'], blank=True, null=True),
                      keep_default=False)

        # Deleting field 'BudgetAssignment.year_and_week'
        db.delete_column('trs_budgetassignment', 'year_and_week')

        # Adding field 'BudgetAssignment.year_week'
        db.add_column('trs_budgetassignment', 'year_week',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trs.YearWeek'], blank=True, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'YearWeek'
        db.delete_table('trs_yearweek')


        # User chose to not deal with backwards NULL issues for 'PersonChange.year_and_week'
        raise RuntimeError("Cannot reverse this migration. 'PersonChange.year_and_week' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'PersonChange.year_and_week'
        db.add_column('trs_personchange', 'year_and_week',
                      self.gf('django.db.models.fields.CharField')(max_length=7, db_index=True),
                      keep_default=False)

        # Deleting field 'PersonChange.year_week'
        db.delete_column('trs_personchange', 'year_week_id')


        # User chose to not deal with backwards NULL issues for 'WorkAssignment.year_and_week'
        raise RuntimeError("Cannot reverse this migration. 'WorkAssignment.year_and_week' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'WorkAssignment.year_and_week'
        db.add_column('trs_workassignment', 'year_and_week',
                      self.gf('django.db.models.fields.CharField')(max_length=7, db_index=True),
                      keep_default=False)

        # Deleting field 'WorkAssignment.year_week'
        db.delete_column('trs_workassignment', 'year_week_id')


        # User chose to not deal with backwards NULL issues for 'Booking.year_and_week'
        raise RuntimeError("Cannot reverse this migration. 'Booking.year_and_week' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Booking.year_and_week'
        db.add_column('trs_booking', 'year_and_week',
                      self.gf('django.db.models.fields.CharField')(max_length=7, db_index=True),
                      keep_default=False)

        # Deleting field 'Booking.year_week'
        db.delete_column('trs_booking', 'year_week_id')


        # User chose to not deal with backwards NULL issues for 'BudgetAssignment.year_and_week'
        raise RuntimeError("Cannot reverse this migration. 'BudgetAssignment.year_and_week' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'BudgetAssignment.year_and_week'
        db.add_column('trs_budgetassignment', 'year_and_week',
                      self.gf('django.db.models.fields.CharField')(max_length=7, db_index=True),
                      keep_default=False)

        # Deleting field 'BudgetAssignment.year_week'
        db.delete_column('trs_budgetassignment', 'year_week_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'Permission'},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'trs.booking': {
            'Meta': {'object_name': 'Booking'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'blank': 'True', 'null': 'True'}),
            'booked_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Person']", 'blank': 'True', 'null': 'True', 'related_name': "'bookings'"}),
            'booked_on': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'blank': 'True', 'null': 'True', 'related_name': "'bookings'"}),
            'hours': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'blank': 'True', 'null': 'True', 'max_digits': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'blank': 'True', 'null': 'True'})
        },
        'trs.budgetassignment': {
            'Meta': {'object_name': 'BudgetAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'blank': 'True', 'null': 'True'}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'blank': 'True', 'null': 'True', 'related_name': "'budget_assignments'"}),
            'budget': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'blank': 'True', 'null': 'True', 'max_digits': '12'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'blank': 'True', 'null': 'True'})
        },
        'trs.person': {
            'Meta': {'ordering': "['name']", 'object_name': 'Person'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'blank': 'True', 'null': 'True'})
        },
        'trs.personchange': {
            'Meta': {'object_name': 'PersonChange'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'blank': 'True', 'null': 'True'}),
            'hours_per_week': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'blank': 'True', 'null': 'True', 'max_digits': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Person']", 'blank': 'True', 'null': 'True', 'related_name': "'person_changes'"}),
            'target': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'blank': 'True', 'null': 'True', 'max_digits': '8'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'blank': 'True', 'null': 'True'})
        },
        'trs.project': {
            'Meta': {'ordering': "['code']", 'object_name': 'Project'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'trs.workassignment': {
            'Meta': {'object_name': 'WorkAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'blank': 'True', 'null': 'True'}),
            'assigned_on': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Project']", 'blank': 'True', 'null': 'True', 'related_name': "'work_assignments'"}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.Person']", 'blank': 'True', 'null': 'True', 'related_name': "'work_assignments'"}),
            'hourly_tariff': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'blank': 'True', 'null': 'True', 'max_digits': '8'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'decimal_places': '2', 'blank': 'True', 'null': 'True', 'max_digits': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_week': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trs.YearWeek']", 'blank': 'True', 'null': 'True'})
        },
        'trs.yearweek': {
            'Meta': {'ordering': "['year', 'week']", 'object_name': 'YearWeek'},
            'first_day': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'week': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['trs']