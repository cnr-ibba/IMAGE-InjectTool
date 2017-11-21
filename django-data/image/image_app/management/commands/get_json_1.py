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
from image_app.models import DictSex, Animals, DictBreeds
from django.core.exceptions import ObjectDoesNotExist
import math

class Command(BaseCommand):
    help = """
    	returns a string containing json formatted data (about animals).    	
    """


    def handle(self, *args, **options):

        # 1. take an animal record (entire dataframe row)
        # 2. read father_id and mother_id and derive animal names
        # 3. return derivedFrom string
        def get_derivedFrom(row):
            father = ''
            mother = ''
            derivedFrom = ''

            if row['father_id'] and not math.isnan(row['father_id']):
                try:
                    father = Animals.objects.get(id=row['father_id']).name
                    derivedFrom = father
                except ObjectDoesNotExist:
                    father = ''

            if row['mother_id'] and not math.isnan(row['mother_id']):
                try:
                    mother = Animals.objects.get(id=row['mother_id']).name
                except ObjectDoesNotExist:
                    mother = ''

            if father and mother:
                derivedFrom += ', '

            derivedFrom += mother

            return derivedFrom



        # open a connection
        engine_to_sampletab = create_engine('postgresql://postgres:***REMOVED***@db:5432/image')

        #======
        #BREEDS
        #======

        df_breeds = pd.read_sql_table('dict_breeds', con=engine_to_sampletab, schema='public')
        df_breeds = df_breeds[['description', 'country', 'species']].rename(
            columns={
                'description': 'suppliedBreed'
            })

        print("'breed':[")

        for index, row in df_breeds.iterrows():
            dict_breed = row.to_dict()
            print('{},'.format(dict_breed))
            if index == 0:
                break
        print("],")


        # =======
        # ANIMALS
        # =======

        df_sex = pd.read_sql_table('dict_sex', con=engine_to_sampletab, schema='public')
        df_animals = pd.read_sql_table('animals', con=engine_to_sampletab, schema='public')

        # convert gender id in gender desc
        # DictSex is a ORM's Object pointing to the dict_sex postgres table
        df_animals['sex'] = df_animals['sex_id'].apply(lambda x: DictSex.objects.get(id=x).description)


        # build derivedFrom information in every rows:
        df_animals['derivedFrom'] = df_animals.apply(lambda row: get_derivedFrom(row), axis=1)
        df_animals['breed'] = df_animals['breed_id'].apply(lambda x: DictBreeds.objects.get(id=x).description)
        df_animals['id'] = df_animals['id'].apply(lambda x: 'temp' + str(x))


        df_animals = df_animals[['id', 'name', 'description', 'breed', 'father_id', 'mother_id',
                                 'derivedFrom', 'farm_latitude', 'farm_longitude', 'sex',
                                 'material', 'birth_location']].rename(
            columns={
                'id': 'biosampleId',
                'farm_latitude': 'birthLocationLatitude',
                'farm_longitude': 'birthLocationLongitude',
                'birth_location': 'birthLocation',
            })

        print("'animal':[")

        for index, row in df_animals.iterrows():

            # row['submission_date'] = row['submission_date'].dt.strftime('%Y-%m-%d')
            # row['submission_date'] = "{0:0>4}-{1:0>2}-{2:0>2}".format(row['submission_date'].year,row['submission_date'].month,
            #                                            row['submission_date'].day)

            dict_animal = row.to_dict()
            # json_animal = row.to_json(date_format='iso')

            print('{},'.format(dict_animal))

            # manage this animal's samples


            if index == 0:
                break
        print("],")


        # =======
        # SAMPLES
        # =======

        df_samples = pd.read_sql_table('samples', con=engine_to_sampletab, schema='public')
        # df_samples['id'] = df_samples['id'].apply(lambda x: 'temp' + str(x))
        df_samples['id'] = df_samples['name']
        df_samples['dataSourceId'] = df_samples['name']
        df_samples['animal'] = df_samples['animal_id'].apply(lambda x: Animals.objects.get(id=x).name)


        # TODO -> read these from login information
        df_samples['dataSource'] = 'CryoWeb'
        df_samples['dataSourceVersion'] = '23.01'
        df_samples['availability'] = 'mailto:peter@ebi.ac.uk'
        # row['submission_date'] = "{0:0>4}-{1:0>2}-{2:0>2}".format(row['submission_date'].year,row['submission_date'].month,
        #                                            row['submission_date'].day)
        # <- TODO

        # df_samples = df_samples[['id', 'name', 'description', 'dataSourceId', 'dataSource',
        #                          'dataSourceVersion', 'animal', 'availability']].rename(
        #     columns={
        #         'id': 'biosampleId',
        #         'animal': 'derivedFrom'
        #     })

        print("'sample':[")

        for index, row in df_samples.iterrows():
            dict_sample = row.to_dict()

            print('{},'.format(dict_sample))

            if index == 0:
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
