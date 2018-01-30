#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 15:46:50 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Revised Andrea Caprera code: get json data using django custom command, ex

$ python manage.py get_json_1

"""


import math
import json
import numpy
import pandas as pd
import datetime

from pandas import Timestamp
from sqlalchemy import create_engine
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

# image models
from image_app.models import DictSex, Animals, DictBreed


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.integer):
            return int(obj)

        elif isinstance(obj, numpy.floating):
            return float(obj)

        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()

        elif isinstance(obj, Timestamp):
            return str(obj)

        else:
            return super(MyEncoder, self).default(obj)


class Command(BaseCommand):
    help = """
    returns a string containing json formatted data (about animals).
    """

    # TODO: is this needed? does index 0 refer to the same object?
    def add_arguments(self, parser):
        """a function to deal with parameters"""

        # Named (optional) arguments
        parser.add_argument(
            '-i',
            '--index',
            default=0,
            type=int,
            help="Get this index (def '%(default)s')",
        )

    def handle(self, *args, **options):

        # define an output variable
        output = dict()

        # get this dataframe index from cmd line
        index = options['index']

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

        def getDictFromDF(df, index):
            row = df.loc[index, ]

            # convert into dictionary
            a_dict = row.to_dict()

            # replace all NaN values (for loating point)
            for k, v in a_dict.items():
                if isinstance(v, numpy.floating):
                    if pd.isna(v):
                        a_dict[k] = None

                elif isinstance(v, datetime.datetime):
                    if pd.isna(v):
                        a_dict[k] = None

            return a_dict

        # open a connection
        # TODO: read parameters from evironment files
        engine_to_sampletab = create_engine(
                'postgresql://postgres:***REMOVED***@db:5432/image')

        # ======
        # BREEDS
        # ======

        df_breeds = pd.read_sql_table(
                'dict_breeds', con=engine_to_sampletab, schema='public')

        # select 3 columns and rename description
        df_breeds = df_breeds[['description', 'country', 'species']].rename(
            columns={
                'description': 'suppliedBreed'
            })

        # take first record from dataframe and convert into dictionary
        output['breed'] = getDictFromDF(df_breeds, index)

        # =======
        # ANIMALS
        # =======

        df_animals = pd.read_sql_table(
                'animals', con=engine_to_sampletab, schema='public')

        # convert gender id in gender desc
        # DictSex is a ORM's Object pointing to the dict_sex postgres table
        df_animals['sex'] = df_animals['sex_id'].apply(
                lambda x: DictSex.objects.get(id=x).description)

        # build derivedFrom information in every rows:
        df_animals['derivedFrom'] = df_animals.apply(
                lambda row: get_derivedFrom(row), axis=1)

        df_animals['breed'] = df_animals['breed_id'].apply(
                lambda x: DictBreed.objects.get(id=x).description)

        df_animals['id'] = df_animals['id'].apply(lambda x: 'temp' + str(x))

        df_animals = df_animals[
            ['id', 'name', 'description', 'breed', 'father_id', 'mother_id',
             'derivedFrom', 'farm_latitude', 'farm_longitude', 'sex',
             'material', 'birth_location']].rename(
            columns={
                'id': 'biosampleId',
                'farm_latitude': 'birthLocationLatitude',
                'farm_longitude': 'birthLocationLongitude',
                'birth_location': 'birthLocation',
            })

        # take first record from dataframe and convert into dictionary
        output['animal'] = getDictFromDF(df_animals, index)

        # =======
        # SAMPLES
        # =======

        df_samples = pd.read_sql_table(
                'samples', con=engine_to_sampletab, schema='public')

        df_samples['id'] = df_samples['name']
        df_samples['dataSourceId'] = df_samples['name']
        df_samples['animal'] = df_samples['animal_id'].apply(
                lambda x: Animals.objects.get(id=x).name)

        # TODO -> read these from login information
        df_samples['dataSource'] = 'CryoWeb'

        # ???: why this values are hard coded?
        df_samples['dataSourceVersion'] = '23.01'
        df_samples['availability'] = 'mailto:peter@ebi.ac.uk'

        # take first record from dataframe and convert into dictionary
        output['sample'] = getDictFromDF(df_samples, index)

        # ==========
        # SUBMISSION
        # ==========

        df_submission = pd.read_sql_table(
                'submissions', con=engine_to_sampletab, schema='public')

        # take first record from dataframe and convert into dictionary
        output['submissions'] = getDictFromDF(df_submission, index)


        # covert output in json
        return json.dumps(output, sort_keys=True, indent=4, allow_nan=False,
                          cls=MyEncoder)
