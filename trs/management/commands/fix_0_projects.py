import logging

from django.core.management.base import BaseCommand

from trs import models
from trs import core

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Fix .0 projects that already have a .1 by moving all the data."

    def handle(self, *args, **options):
        project_codes = models.Project.objects.all().values_list(
            'code', flat=True)
        dot_zero_codes = set([code[:-2] for code in project_codes
                              if code.endswith('.0')])
        dot_one_codes = set([code[:-2] for code in project_codes
                             if code.endswith('.1')])
        codes_with_both = dot_zero_codes & dot_one_codes
        for code in codes_with_both:
            zero_project = models.Project.objects.get(code=code + '.0')
            one_project = models.Project.objects.get(code=code + '.1')
            print("==========================================")
            print("Van:  %s %s" % (zero_project, zero_project.description))
            print("Naar: %s %s" % (one_project, one_project.description))
            # Invoices
            invoices = models.Invoice.objects.filter(project=zero_project)
            if invoices:
                print("Facturen:")
                for invoice in invoices:
                    print("    %s" % invoice)
            # Budget items
            budget_items = models.BudgetItem.objects.filter(project=zero_project)
            if budget_items:
                print("Begrotingsitems:")
                for budget_item in budget_items:
                    print("    %s" % budget_item)
            # Bookings
            bookings = models.Booking.objects.filter(booked_on=zero_project)
            if bookings:
                print("Boekingen:")
                for booking in bookings:
                    print("    %s uur door %s" % (booking.hours, booking.booked_by))
            # Work assignments
            work_assignments = models.WorkAssignment.objects.filter(assigned_on=zero_project)
            if work_assignments:
                print("Werktoekenningen:")
                for work_assignment in work_assignments:
                    print("    %s uur aan %s" % (work_assignment.hours, work_assignment.assigned_to))
