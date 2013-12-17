import datetime

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


class ProjectFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.Project

    code = 'P1234'
    description = ''
    internal = False
    archived = False
    principal = ''
    project_leader = None
    project_manager = None


class YearWeekFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.YearWeek

    year = 2013
    # Start in week 2, which starts 7 jan 2013.
    week = factory.Sequence(lambda n: n + 1)
    first_day = factory.Sequence(
        lambda n: (datetime.date(year=2013, month=1, day=7) +
                  datetime.timedelta(days=7) * n))


class PersonChangeFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.PersonChange

    hours_per_week = 0
    target = 0
    year_week = factory.SubFactory(YearWeekFactory)


class BookingFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.Booking


class WorkAssignmentFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.WorkAssignment

    hours = 0
    hourly_tariff = 0


class BudgetItemFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.BudgetItem
