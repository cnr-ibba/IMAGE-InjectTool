
import logging

from django.core.management import BaseCommand

from image_app import helper
from image_app.models import DataSource

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
        imagedb = helper.ImageDB()

        # estabilishing a connection
        conn = imagedb.get_connection()

        # TODO: move add prefix image_app to django modeled image tables
        # HINT: maybe UID or InjectTools could be more informative than
        # image_app suffix?

        if options['all'] is True:
            logger.info("Truncating all image tables...")

            # HINT: image_app_person, image_app_organization and
            # image_app_person_organizations haven't to be deleted or user
            # registered in django admin will not work anymore
            statement = """
                    TRUNCATE image_app_animal,
                             image_app_database,
                             image_app_datasource,
                             image_app_dictbreed,
                             image_app_dictcountry,
                             image_app_dictrole,
                             image_app_dictsex,
                             image_app_dictspecie,
                             image_app_name,
                             image_app_ontology,
                             image_app_publication,
                             image_app_sample,
                             image_app_submission RESTART IDENTITY
                        """

        else:
            logger.info("Truncating filled image tables...")

            statement = """
                    TRUNCATE image_app_animal,
                             image_app_dictbreed,
                             image_app_name,
                             image_app_sample,
                             image_app_dictspecie,
                             image_app_submission RESTART IDENTITY
                        """

        # debug
        logger.debug("Executing: %s" % (statement))

        # start a transaction
        trans = conn.begin()
        conn.execute(statement)
        trans.commit()

        # unset loaded flag from data source
        for datasource in DataSource.objects.all():
            datasource.loaded = False
            datasource.save()

        # debug
        logger.info("Done!")
