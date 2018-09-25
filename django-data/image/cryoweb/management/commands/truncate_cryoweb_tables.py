
import logging

from django.core.management import BaseCommand

from cryoweb.models import truncate_database

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Truncate all tables in the cryoweb db"""

    def handle(self, *args, **options):
        logger.info("Starting truncate_cryoweb_tables")

        truncate_database()

        logger.info("Done!")
