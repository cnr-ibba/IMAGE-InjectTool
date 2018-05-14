#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  9 16:58:01 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import pandas as pd
from django.contrib.messages import get_messages
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from image_app import helper
from image_app.models import DictCountry, DictSpecie, User
from image_app.views.cryoweb import (fill_countries, fill_species,
                                     get_a_datasource)

from language.models import SpecieSynonim


class BaseTestCase(TestCase):
    # import this file and populate database once
    fixtures = []

    # By default, fixtures are only loaded into the default database. If you
    # are using multiple databases and set multi_db=True, fixtures will be
    # loaded into all databases.
    multi_db = True

    # https://docs.djangoproject.com/en/1.11/topics/testing/advanced/#example
    def setUp(self):
        """Connect to client"""
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='test', email='test@test.com', password='test')

        self.client = Client()
        self.client.login(username='test', password='test')


class FillUIDTestClass(BaseTestCase):
    # import this file and populate database once
    fixtures = [
        "cryoweb.json", "dictcountry.json", "datasource.json", "dictsex.json",
        "dictspecie.image.json", "speciesynonim.image.json"
    ]

    def setUp(self):
        """Setting up"""

        # calling my base class setup
        super().setUp()

        # define helper database objects
        cryowebdb = helper.CryowebDB()

        # set those values using a function from helper objects
        self.engine_from_cryoweb = cryowebdb.get_engine()

        # TODO: get datasource to load from link or admin
        self.datasource = get_a_datasource()

        self.context = {
                # get username from request.
                'username': self.user.username,
                'loaded': {},
                'warnings': {},
                'has_warnings': False}

    def test_cryoweb_already_imported(self):
        # Create an instance of a GET request.
        # request = self.factory.get(reverse('image_app:upload_cryoweb'))

        # Recall that middleware are not supported. You can simulate a
        # logged-in user by setting request.user manually.
        # request.user = self.user

        # Test upload_cryoweb() as if it were deployed at
        # reverse('image_app:upload_cryoweb')
        # response = upload_cryoweb(request)

        # same thing, but with a client request
        response = self.client.get(
                reverse('image_app:upload_cryoweb'))

        # each element is an instance
        # of django.contrib.messages.storage.base.Message
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        for message in all_messages:
            self.assertEqual(message.tags, "warning")
            self.assertEqual(
                    message.message,
                    "cryoweb mirror database has data. Ignoring data load")

    def test_import_into_UID(self):
        """Import loaded cryoweb data into UID"""

        response = self.client.get(
                reverse('image_app:import_from_cryoweb'))

        self.assertFalse("error" in response.context)

    def test_load_species(self):
        """Testing load_species function"""

        # define a custum df for species
        test_df = pd.DataFrame({'efabis_species': ['Cattle', 'Sheep']})

        # concat dataframe two times
        test_df = pd.concat([test_df, test_df])

        # read species from table
        reference = []

        # get specie using synonyms (loaded using fixtures)
        for synonim in test_df["efabis_species"]:
            dictspecie = DictSpecie.get_by_synonim(synonim, "Germany")
            reference += [dictspecie.id]

        # call function and get a list with primary keys
        test = fill_species(test_df, self.context, self.datasource)

        # testing equality
        self.assertEqual(reference, test)

    def test_load_countriess(self):
        """Testing load_countries function"""

        # read the the v_breeds_species view in the "cryoweb database"
        df_breeds_species = pd.read_sql_table(
                'v_breeds_species',
                con=self.engine_from_cryoweb,
                schema="apiis_admin")

        # read species from table
        reference = []

        for country in df_breeds_species["efabis_country"]:
            dictcountry, status = DictCountry.objects.get_or_create(
                    label=country)
            reference += [dictcountry.id]

        # call function and get a list with primary keys
        test = fill_countries(df_breeds_species, self.context)

        # testing equality
        self.assertEqual(reference, test)
