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
            core.get_pyc(person)
            logger.info("%s out of %s done", index + 1, num_persons)
