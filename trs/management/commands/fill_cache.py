import logging

from django.core.management.base import BaseCommand

from trs import models
from trs import core

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Pre-fill the cache. Takes a horrid long time."

    def handle(self, *args, **options):
        num_persons = models.Person.objects.all().count()
        logger.info("%s persons in total.", num_persons)
        for index, person in enumerate(models.Person.objects.all()):
            person.to_book()
            person.to_work_up_till_now()
            core.get_pyc(person)
            logger.info("%s out of %s done", index + 1, num_persons)

        num_projects = models.Project.objects.all().count()
        logger.info("%s projects in total.", num_projects)
        for index, project in enumerate(models.Project.objects.all()):
            project.work_calculation()
            project.not_yet_started()
            project.already_ended()
            logger.info("%s out of %s done", index + 1, num_projects)
