
from django.core.management import BaseCommand

from image_app import helper


class Command(BaseCommand):
    help = """Truncate image_app tables"""

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            help='Truncate all image_app tables',
        )

    def handle(self, *args, **options):
        imagedb = helper.ImageDB()

        # estabilishing a connection
        conn = imagedb.get_connection()

        # TODO: move add prefix image_app to django modeled image tables
        # HINT: maybe UID or InjectTools could be more informative than
        # image_app suffix?

        if options['all'] is True:
            print("Truncating all image tables...")

            statement = """
                    TRUNCATE image_app_animal,
                             image_app_database,
                             image_app_datasource,
                             image_app_dictbreed,
                             image_app_dictrole,
                             image_app_dictsex,
                             image_app_name,
                             image_app_organization,
                             image_app_organization_users,
                             image_app_person,
                             image_app_publication,
                             image_app_sample,
                             image_app_submission,
                             image_app_term_source
                        """

        else:
            print("Truncating filled image tables...")

            statement = """
                    TRUNCATE image_app_animal,
                             image_app_dictbreed,
                             image_app_name,
                             image_app_sample,
                             image_app_submission
                        """

        # start a transaction
        trans = conn.begin()
        conn.execute(statement)
        trans.commit()
        print("Done!")
