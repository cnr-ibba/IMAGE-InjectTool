from django.core.management import BaseCommand
import os
import glob
import unittest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import pprint
import subprocess
from django.conf import settings
from sqlalchemy import exc
import sys

class Command(BaseCommand):
    help = """
    	Truncate all tables in the imported_from_cryoweb db
    """

    def handle(self, *args, **options):

        engine_from_cryoweb = create_engine('postgresql://postgres:***REMOVED***@db:5432/imported_from_cryoweb')
        num_animals = pd.read_sql_query('select count(*) as num from animal', con=engine_from_cryoweb)

        num_animals = num_animals['num'].values[0]
        print("animals num:\n{}".format(num_animals))

        if num_animals > 0:
            statement = text(""" TRUNCATE "animal", "ar_constraints", "ar_dbtdescriptors", "ar_dbtpolicies", "ar_dbttables", "ar_role_constraints", "ar_role_dbtpolicies", "ar_role_stpolicies", "ar_roles", "ar_stpolicies", "ar_user_roles", "ar_users", "ar_users_data", "blobs", "breeds_species", "codes", "contacts", "event", "inspool", "inspool_err", "languages", "load_stat", "locations", "movements", "new_pest", "nodes", "protocols", "sources", "status_changes", "storage", "storage_history", "targets", "transfer", "unit", "vessels", "vessels_storage"; """)

            print(statement)
            try:
                with engine_from_cryoweb.begin() as connection:
                    r = connection.execute(statement)
            except exc.SQLAlchemyError:
                sys.exit("Encountered general SQLAlchemyError")

