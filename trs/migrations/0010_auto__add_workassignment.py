# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'WorkAssignment'
        db.create_table('trs_workassignment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(blank=True, auto_now_add=True)),
            ('added_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['auth.User'], null=True)),
            ('year_and_week', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=7)),
            ('hours', self.gf('django.db.models.fields.DecimalField')(blank=True, max_digits=8, decimal_places=2, null=True)),
            ('hourly_tariff', self.gf('django.db.models.fields.DecimalField')(blank=True, max_digits=8, decimal_places=2, null=True)),
            ('assigned_on', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='work_assignments', to=orm['trs.Project'], null=True)),
            ('assigned_to', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='work_assignments', to=orm['trs.Person'], null=True)),
        ))
        db.send_create_signal('trs', ['WorkAssignment'])


    def backwards(self, orm):
        # Deleting model 'WorkAssignment'
        db.delete_table('trs_workassignment')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'})
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
            'Meta': {'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'trs.booking': {
            'Meta': {'object_name': 'Booking'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'booked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bookings'", 'to': "orm['trs.Person']", 'null': 'True'}),
            'booked_on': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bookings'", 'to': "orm['trs.Project']", 'null': 'True'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_and_week': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '7'})
        },
        'trs.person': {
            'Meta': {'object_name': 'Person', 'ordering': "['name']"},
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'trs.personchange': {
            'Meta': {'object_name': 'PersonChange'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'hours_per_week': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'person_changes'", 'to': "orm['trs.Person']", 'null': 'True'}),
            'target': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'year_and_week': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '7'})
        },
        'trs.project': {
            'Meta': {'object_name': 'Project', 'ordering': "['code']"},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'trs.workassignment': {
            'Meta': {'object_name': 'WorkAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['auth.User']", 'null': 'True'}),
            'assigned_on': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'work_assignments'", 'to': "orm['trs.Project']", 'null': 'True'}),
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'work_assignments'", 'to': "orm['trs.Person']", 'null': 'True'}),
            'hourly_tariff': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'hours': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'max_digits': '8', 'decimal_places': '2', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year_and_week': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '7'})
        }
    }

    complete_apps = ['trs']