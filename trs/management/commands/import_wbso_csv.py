import csv
import datetime
import logging

from django.core.management.base import BaseCommand

from trs import models

logger = logging.getLogger(__name__)

OVERWRITE_EXISTING = False


def get_or_create_wbso_project(wbso_number):
    number = int(wbso_number)
    matching = models.WbsoProject.objects.filter(number=number)
    if matching:
        return matching[0]
    wbso_project = models.WbsoProject(
        number=number,
        title="TODO titel voor %s" % wbso_number,
        start_date=datetime.date(2013, 1, 1),
        end_date=datetime.date(2015, 12, 31))
    wbso_project.save()
    logger.info("Created WBSO project %s", wbso_project)
    return wbso_project


class Command(BaseCommand):
    args = ".csv file"
    help = "Pre-fill the cache. Takes a horrid long time."

    def handle(self, *args, **options):
        filename = args[0]
        logger.info("Reading from %s", filename)
        for project_code, wbso_number, wbso_percentage in self.extract(filename):
            wbso_project = get_or_create_wbso_project(wbso_number)
            try:
                project = models.Project.objects.get(code__iexact=project_code)
            except models.Project.DoesNotExist:
                logger.warn("Project %s does not exist", project_code)
                continue
            percentage = wbso_percentage.replace('%', '')
            if not percentage:
                percentage = 0
            percentage = int(percentage)
            if project.wbso_project and not OVERWRITE_EXISTING:
                logger.debug("Not overwriting existing wbso project %s on %s",
                             wbso_project, project)
                continue
            project.wbso_project = wbso_project
            project.wbso_percentage = percentage
            project.save()
            logger.info("Set wbso project %s on %s for %s%%",
                        wbso_project, project, percentage)


    def extract(self, filename):
        with open(filename) as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) != 12:
                    # Empty line.
                    continue
                if row[0] == 'Code':
                    # First line
                    continue
                code = row[0]
                wbso = row[7]
                percentage = row[9]
                if not wbso:
                    continue
                yield (code, wbso, percentage)
