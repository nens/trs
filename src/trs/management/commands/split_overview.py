import logging

import xlsxwriter
from django.core.management.base import BaseCommand
from django.db.models import Sum

from trs import models

YEAR = 2022
FILENAME = "var/split_overview.xlsx"

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Export spreadsheet for handling the split it/consultancy"

    def handle(self, *args, **options):
        bookings = models.Booking.objects.filter(year_week__year=YEAR)
        hours_per_person_per_projectgroup = bookings.values(
            "booked_by__group__name", "booked_by__name", "booked_on__group__name"
        ).annotate(Sum("hours"))
        # Per person: what it says.
        # Per projectgroup: the group of the projects being booked on.
        groups = (
            bookings.order_by("booked_on__group__name")
            .distinct()
            .values_list("booked_on__group__name", flat=True)
        )

        header_line = ["Naam", "Groep", "Groep van project =>"] + list(groups)

        persons = {}
        for query_result in hours_per_person_per_projectgroup:
            name = query_result["booked_by__name"]
            if name not in persons:
                persons[name] = {
                    "group": query_result["booked_by__group__name"],
                    "booked_per_projectgroup": {},
                }
            persons[name]["booked_per_projectgroup"][
                query_result["booked_on__group__name"]
            ] = query_result["hours__sum"]

        workbook = xlsxwriter.Workbook(FILENAME)
        worksheet = workbook.add_worksheet()

        worksheet.write_row(0, 0, header_line)
        for i, name in enumerate(persons):
            person = persons[name]
            line = [name, person["group"], ""]
            for group in groups:
                line.append(person["booked_per_projectgroup"].get(group, 0))

            worksheet.write_row(i + 1, 0, line)

        workbook.close()
        print(f"Wrote {FILENAME}")
