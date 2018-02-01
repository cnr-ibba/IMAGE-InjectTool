
from django.core.management import BaseCommand
from sqlalchemy import create_engine


class Command(BaseCommand):
    help = """Truncate all tables in the imported_from_cryoweb db"""

    def handle(self, *args, **options):
        engine_from_cryoweb = create_engine(
                'postgresql://postgres:***REMOVED***@db:5432/'
                'imported_from_cryoweb')

        # estabilishing a connection and change default schema
        conn = engine_from_cryoweb.connect()
        conn.execute("SET search_path TO apiis_admin, public")

        print("Truncating imported_from_cryoweb tables...")

        statement = """
                TRUNCATE animal,
                         ar_constraints,
                         ar_dbtdescriptors,
                         ar_dbtpolicies,
                         ar_dbttables,
                         ar_role_constraints,
                         ar_role_dbtpolicies,
                         ar_role_stpolicies,
                         ar_roles,
                         ar_stpolicies,
                         ar_user_roles,
                         ar_users,
                         ar_users_data,
                         blobs,
                         breeds_species,
                         codes,
                         contacts,
                         event,
                         inspool,
                         inspool_err,
                         languages,
                         load_stat,
                         locations,
                         movements,
                         new_pest,
                         nodes,
                         protocols,
                         sources,
                         status_changes,
                         storage,
                         storage_history,
                         targets,
                         transfer,
                         unit,
                         vessels,
                         vessels_storage
                    """

        # start a transaction
        trans = conn.begin()
        conn.execute(statement)
        trans.commit()
        print("Done!")
