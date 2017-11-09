from django.core.management import BaseCommand
import os
import glob
import unittest
import pandas as pd
from sqlalchemy import create_engine
import pprint
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

        # read the dict_breeds table
        df_breeds = pd.read_sql_table('dict_breeds', con=engine_to_sampletab, schema='public')
        print("'breed':[")

        for index, row in df_breeds.iterrows():

            dict_breed = row.to_dict()

            print('{},'.format(dict_breed))

            if index == 2:
                break
        print("],")

        # read the animals table
        df_animals = pd.read_sql_table('animals', con=engine_to_sampletab, schema='public')
        print("'animal':[")

        for index, row in df_animals.iterrows():


            # row['submission_date'] = row['submission_date'].dt.strftime('%Y-%m-%d')
            row['submission_date'] = "{0:0>4}-{1:0>2}-{2:0>2}".format(row['submission_date'].year,row['submission_date'].month,
                                                       row['submission_date'].day)

            dict_animal = row.to_dict()
            # json_animal = row.to_json(date_format='iso')

            print('{},'.format(dict_animal))

            # manage this animal's samples


            if index == 2:
                break
        print("],")


        df_samples = pd.read_sql_table('samples', con=engine_to_sampletab, schema='public')
        print("'sample':[")

        for index, row in df_samples.iterrows():
            dict_sample = row.to_dict()
            # json_animal = row.to_json(date_format='iso')

            print('{},'.format(dict_sample))

            if index == 2:
                break

        print("]\n")

        # jsonstring = df_animals.to_json(orient='records')
        # df_breeds = pd.read_sql_table('dict_breeds', con=engine_to_sampletab, schema='public')
        # jsonstring = df_breeds.to_json(orient='records')



        # df_samples = pd.read_sql_table('samples', con=engine_to_sampletab, schema='public')
        #
        # jsonstring = df_samples.to_json(orient='records')
        # return jsonstring

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
