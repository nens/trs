from haystack import indexes

from trs import models


class ProjectIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return models.Project

    def prepare(self, obj):
        data = super(ProjectIndex, self).prepare(obj)
        if obj.archived:
            # Push archived objects down.
            data['boost'] = 0.5
        return data


class PersonIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return models.Person

    def prepare(self, obj):
        data = super(PersonIndex, self).prepare(obj)
        if obj.archived:
            # Push archived objects down.
            data['boost'] = 0.5
        return data
