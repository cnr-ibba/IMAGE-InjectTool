from django.core.management import BaseCommand
import os
import glob
import unittest
import pandas as pd
from sqlalchemy import create_engine
# import pprint
import subprocess
from django.conf import settings
from django.core.management import call_command

class Command(BaseCommand):
    help = """
    	returns a string containing json formatted data (about animals).
    	
    """

    def handle(self, *args, **options):

        # open a connection
        engine_to_sampletab = create_engine('postgresql://postgres:***REMOVED***@db:5432/image')

        # read the animal view in the "imported from Cryoweb" database
        # this needs to be changed in the future with the
        # animal table in the unified internal database - only for format check now


        # df_animals = pd.read_sql_table('animals', con=engine_to_sampletab, schema='public')
        # jsonstring = df_animals.to_json(orient='records')
        # df_breeds = pd.read_sql_table('dict_breeds', con=engine_to_sampletab, schema='public')
        # jsonstring = df_breeds.to_json(orient='records')
        df_samples = pd.read_sql_table('samples', con=engine_to_sampletab, schema='public')
        jsonstring = df_samples.to_json(orient='records')
        return jsonstring

        # engine_to_sampletab = create_engine('postgresql://postgres:***REMOVED***@db:5432/image')
        #
        # # get the file list from the filesystem
        # os.chdir(settings.MEDIA_ROOT)
        # ls_from_filesys = glob.glob("backups/*.sql")
        # print("ls_from_filesys:\n{}".format(ls_from_filesys))
        #
        # # get the file list from the db
        # ls_from_db = pd.read_sql_query('select backup from image_app_backup', con=engine_to_sampletab)
        # ls_from_db = list(ls_from_db['backup'])
        # print("ls_from_db:\n{}".format(ls_from_db))
        #
        # for elem in ls_from_filesys:
        #     if elem not in ls_from_db:
        #         os.remove(elem)
        #
        # call_command('mycheck')
