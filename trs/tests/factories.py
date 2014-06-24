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


class ProjectFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.Project

    code = factory.Sequence(lambda n: 'P%s' % str(1234 + n))
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

    person = factory.SubFactory(PersonFactory)
    hours_per_week = 0
    target = 0
    year_week = factory.SubFactory(YearWeekFactory)


class BookingFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.Booking

    booked_by = factory.SubFactory(PersonFactory)
    booked_on = factory.SubFactory(ProjectFactory)


class WorkAssignmentFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.WorkAssignment

    hours = 0
    hourly_tariff = 0
    assigned_to = factory.SubFactory(PersonFactory)
    assigned_on = factory.SubFactory(ProjectFactory)


class BudgetItemFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.BudgetItem

    project = factory.SubFactory(ProjectFactory)
