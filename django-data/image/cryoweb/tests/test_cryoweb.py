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
from django.core.management import call_command

import cryoweb.helpers

import image_app.helpers

from image_app.models import DictCountry, DictSpecie, User
from ..views import (fill_countries, fill_species, get_a_submission)

from language.models import SpecieSynonim


class BaseTestCase(TestCase):
    # import this file and populate database once
    fixtures = []

    # By default, fixtures are only loaded into the default database. If you
    # are using multiple databases and set multi_db=True, fixtures will be
    # loaded into all databases. However, this will raise problems when
    # managing extended user models
    multi_db = False

    # https://docs.djangoproject.com/en/1.11/topics/testing/advanced/#example
    def setUp(self):
        """Connect to client"""
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.get(username="test")
        self.client = Client()
        self.client.login(username='test', password='test')

    def check_messages(self, response, tag, message_text):
        """Check that a response has warnings"""

        # each element is an instance
        # of django.contrib.messages.storage.base.Message
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        for message in all_messages:
            self.assertTrue(tag in message.tags)
            self.assertEqual(
                message.message,
                message_text)


class FillUIDTestClass(BaseTestCase):
    # import this file and populate database once
    fixtures = [
        "cryoweb/user",
        "cryoweb/dictrole",
        "cryoweb/organization",
        "cryoweb/dictcountry",
        "cryoweb/submission",
        "cryoweb/dictsex",
        "cryoweb/dictspecie",
        "cryoweb/speciesynonim"
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        # this fixture have to be loaded in a secondary (test) database,
        # I can't upload it using names and fixture section, so it will
        # be added manually using loaddata
        call_command(
            'loaddata',
            'cryoweb/cryoweb.json',
            app='cryoweb',
            database='cryoweb',
            verbosity=0)

    def setUp(self):
        """Setting up"""

        # calling my base class setup
        super().setUp()

        # define helper database objects
        cryowebdb = image_app.helpers.CryowebDB()

        # set those values using a function from helper objects
        self.engine_from_cryoweb = cryowebdb.get_engine()

        # TODO: get submission to load from link or admin
        self.submission = get_a_submission()

        self.context = {
            # get username from request.
            'username': self.user.username,
            'loaded': {},
            'warnings': {},
            'has_warnings': False}

    def test_cryoweb_already_imported(self):
        # Create an instance of a GET request.
        # request = self.factory.get(reverse('cryoweb:upload_cryoweb'))

        # Recall that middleware are not supported. You can simulate a
        # logged-in user by setting request.user manually.
        # request.user = self.user

        # Test upload_cryoweb() as if it were deployed at
        # reverse('cryoweb:upload_cryoweb')
        # response = upload_cryoweb(request)

        # same thing, but with a client request
        response = self.client.get(
            reverse('cryoweb:upload_cryoweb'))

        self.check_messages(
            response,
            "warning",
            "cryoweb mirror database has data. Ignoring data load")

    def test_import_into_UID(self):
        """Import loaded cryoweb data into UID"""

        response = self.client.get(
            reverse('cryoweb:import_from_cryoweb'))

        self.assertFalse("error" in response.context)

    def test_all_ds_imported(self):
        """No submissions left to import"""

        response = self.client.get(
            reverse('cryoweb:import_from_cryoweb'))

        # TODO: after data import into UID , cryoweb stage area need to be
        # truncated. chech that this condition is true
#        response = self.client.get(
#            reverse('cryoweb:upload_cryoweb'))
#
#        self.check_messages(
#            response,
#            "warning",
#            "all submissions were loaded")

        response = self.client.get(
            reverse('cryoweb:import_from_cryoweb'))

        self.check_messages(
            response,
            "warning",
            "all submissions were loaded")

    def test_import_into_UID_no_specie_synomims(self):
        """testing importing into UID without sysnonims"""

        # now delete a synonim
        synonim = SpecieSynonim.objects.get(
            language__label='Germany',
            word='Cattle')
        synonim.delete()

        response = self.client.get(
            reverse('cryoweb:import_from_cryoweb'))

        self.check_messages(
            response,
            "error",
            "Some species haven't a synonim!")

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
        test = fill_species(test_df, self.context, self.submission)

        # testing equality
        self.assertEqual(reference, test)

    def test_check_species(self):
        """Testing species and synonims"""

        self.assertTrue(cryoweb.helpers.check_species("Germany"))

        # now delete a synonim
        synonim = SpecieSynonim.objects.get(
            language__label='Germany',
            word='Cattle')
        synonim.delete()

        self.assertFalse(cryoweb.helpers.check_species("Germany"))

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
