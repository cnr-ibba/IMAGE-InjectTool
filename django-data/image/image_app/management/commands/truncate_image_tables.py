from django.core.management import BaseCommand, CommandError
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
    	Truncate animals, samples and dict_breeds tables
    """

    def handle(self, *args, **options):

        engine_to_sampletab = create_engine('postgresql://postgres:***REMOVED***@db:5432/image')
        num_animals = pd.read_sql_query('select count(*) as num from animals', con=engine_to_sampletab)

        num_animals = num_animals['num'].values[0]
        print("animals num:\n{}".format(num_animals))

        if num_animals > 0:
            statement = text(""" TRUNCATE animals, dict_breeds, samples; """)

            print(statement)
            try:
                with engine_to_sampletab.begin() as connection:
                    r = connection.execute(statement)
            except Exception:
                raise CommandError('Encountered general SQLAlchemyError')

        # call_command('mycheck')

