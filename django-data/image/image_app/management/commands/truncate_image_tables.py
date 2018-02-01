
from django.core.management import BaseCommand
from sqlalchemy import create_engine


class Command(BaseCommand):
    help = """Truncate animals, samples and dict_breeds tables"""

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
                TRUNCATE animals,
                         databases,
                         image_app_datasource,
                         image_app_dictbreed,
                         image_app_dictrole,
                         image_app_dictsex,
                         image_app_name,
                         organizations,
                         persons,
                         publications,
                         samples,
                         submissions,
                         term_sources
                    """

        # start a transaction
        trans = conn.begin()
        conn.execute(statement)
        trans.commit()
        print("Done!")
