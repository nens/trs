# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Person.slug'
        db.add_column('trs_person', 'slug',
                      self.gf('django.db.models.fields.SlugField')(default='a', max_length=50),
                      keep_default=False)

        # Adding field 'Person.name'
        db.add_column('trs_person', 'name',
                      self.gf('django.db.models.fields.CharField')(default='a', max_length=255),
                      keep_default=False)

        # Adding field 'Person.description'
        db.add_column('trs_person', 'description',
                      self.gf('django.db.models.fields.CharField')(blank=True, default='', max_length=255),
                      keep_default=False)

        # Adding field 'Project.slug'
        db.add_column('trs_project', 'slug',
                      self.gf('django.db.models.fields.SlugField')(default='a', max_length=50),
                      keep_default=False)

        # Adding field 'Project.code'
        db.add_column('trs_project', 'code',
                      self.gf('django.db.models.fields.CharField')(default='a', max_length=255),
                      keep_default=False)

        # Adding field 'Project.description'
        db.add_column('trs_project', 'description',
                      self.gf('django.db.models.fields.CharField')(blank=True, default='', max_length=255),
                      keep_default=False)

        # Adding field 'Project.added'
        db.add_column('trs_project', 'added',
                      self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime(2013, 10, 25, 0, 0), auto_now_add=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Person.slug'
        db.delete_column('trs_person', 'slug')

        # Deleting field 'Person.name'
        db.delete_column('trs_person', 'name')

        # Deleting field 'Person.description'
        db.delete_column('trs_person', 'description')

        # Deleting field 'Project.slug'
        db.delete_column('trs_project', 'slug')

        # Deleting field 'Project.code'
        db.delete_column('trs_project', 'code')

        # Deleting field 'Project.description'
        db.delete_column('trs_project', 'description')

        # Deleting field 'Project.added'
        db.delete_column('trs_project', 'added')


    models = {
        'trs.person': {
            'Meta': {'object_name': 'Person'},
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'trs.project': {
            'Meta': {'object_name': 'Project'},
            'added': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['trs']