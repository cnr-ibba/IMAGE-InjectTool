
from django.core.management import BaseCommand
from sqlalchemy import create_engine


class Command(BaseCommand):
    help = """Truncate all image_app tables"""

    def handle(self, *args, **options):

        engine_to_sampletab = create_engine(
                'postgresql://postgres:***REMOVED***@db:5432/image')

        # estabilishing a connection
        conn = engine_to_sampletab.connect()

        print("Truncating image tables...")

        # TODO: move add prefix image_app to django modeled image tables
        # HINT: maybe UID or InjectTools could be more informative than
        # image_app suffix?
        statement = """
                TRUNCATE databases,
                         image_app_animal,
                         image_app_datasource,
                         image_app_dictbreed,
                         image_app_dictrole,
                         image_app_dictsex,
                         image_app_name,
                         image_app_sample,
                         organizations,
                         persons,
                         publications,
                         submissions,
                         term_sources
                    """

        # start a transaction
        trans = conn.begin()
        conn.execute(statement)
        trans.commit()
        print("Done!")
