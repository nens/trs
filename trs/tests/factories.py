import factory
from django.contrib.auth.models import User

from trs import models


class UserFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = User
    username = factory.Sequence(lambda n: 'user{0}'.format(n))


class PersonFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.Person

    name = 'Reinout'
    user = factory.SubFactory(UserFactory)
    login_name = 'reinout.vanrees'
    slug = 'reinoutvanrees'


class ProjectFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.Project

    code = 'P1234'
    slug = 'p1234'
