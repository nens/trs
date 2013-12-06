from django.core.management.base import BaseCommand
from django.conf import settings

from trs import models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Import the xls exports from the old TRS"

    def handle(self, *args, **options):
        pass
