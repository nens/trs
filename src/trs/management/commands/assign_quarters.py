# Used to automatically book 40 hours on an internal project for managers.
import logging

from django.core.management.base import BaseCommand
from django.db import models

from trs.models import Booking, Project, WorkAssignment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Assign last quarter's users to the current one"

    def add_arguments(self, parser):
        parser.add_argument("previous_year", type=str)
        parser.add_argument("previous_quarter", type=str)
        parser.add_argument("next_year", type=str)
        parser.add_argument("next_quarter", type=str)

    def handle(self, *args, **options):
        previous_projects = Project.objects.filter(
            code__startswith=options["previous_year"],
            code__endswith=options["previous_quarter"],
        )
        for previous_project in previous_projects:
            previous_code = previous_project.code
            next_code = previous_code.replace(
                options["previous_year"], options["next_year"]
            ).replace(options["previous_quarter"], options["next_quarter"])
            next_project = Project.objects.get(code=next_code)
            print()
            print(next_code)
            print()

            for member in previous_project.members.all():
                hours_booked = (
                    Booking.objects.filter(
                        booked_by=member, booked_on=previous_project
                    ).aggregate(models.Sum("hours"))["hours__sum"]
                    or 0
                )
                if member not in next_project.members.all():
                    print(f"Adding {member} with {hours_booked} budget")
                    WorkAssignment.objects.create(
                        hours=hours_booked,
                        hourly_tariff=member.standard_hourly_tariff(),
                        assigned_on=next_project,
                        assigned_to=member,
                    )
