
import logging

from django.core.management import BaseCommand

from image_app.models import truncate_database, truncate_filled_tables

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Truncate image_app tables and reset counters"""

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            help='Truncate all image_app tables and reset counters',
        )

    def handle(self, *args, **options):
        # HINT: maybe UID or InjectTools could be more informative than
        # image_app suffix?

        logger.info("Starting truncate_image_tables")

        if options['all'] is True:
            truncate_database()

        else:
            truncate_filled_tables()

        # debug
        logger.info("Done!")
