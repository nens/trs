# Used to automatically book 40 hours on an internal project for managers.
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Sum

from trs import models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Book 40 hours for the managers on a hardcoded internal project."

    def handle(self, *args, **options):
        # Hardcoded year, change this every year.
        year = 2015
        # Hardcoded project ID, change this every year.
        bedrijfsvoering = 4613
        # Hardcoded user IDs.
        bastiaan = 3
        fons = 6
        wytze = 8

        import_user = User.objects.get(username='import_user')

        year_weeks = models.YearWeek.objects.filter(year=year)
        project = models.Project.objects.get(pk=bedrijfsvoering)
        for person_id in [bastiaan, fons, wytze]:
            person = models.Person.objects.get(pk=person_id)
            to_work = person.hours_per_week()
            for year_week in year_weeks:
                to_work_this_week = to_work - year_week.num_days_missing * 8
                already_booked = round(models.Booking.objects.filter(
                    booked_by=person,
                    year_week=year_week).aggregate(
                        Sum('hours'))['hours__sum'] or 0)
                to_book = to_work_this_week - already_booked
                if to_book:
                    logger.info("Booking %s hours on %s in week %s for %s",
                                to_book, project, year_week, person)
                    booking = models.Booking(
                        booked_by=person,
                        booked_on=project,
                        hours=to_book,
                        year_week=year_week,
                        added_by=import_user)
                    booking.save()
