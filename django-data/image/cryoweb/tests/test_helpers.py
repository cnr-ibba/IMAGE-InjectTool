#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 20 16:01:04 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

# --- import

from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from language.models import SpecieSynonim
from image_app.models import Submission, DictBreed, Name, Animal, Sample

from ..helpers import (
    upload_cryoweb, check_species, CryoWebImportError, cryoweb_import)
from ..models import db_has_data, truncate_database


class BaseTestCase():
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

    # By default, fixtures are only loaded into the default database. If you
    # are using multiple databases and set multi_db=True, fixtures will be
    # loaded into all databases. However, this will raise problems when
    # managing extended user models
    multi_db = False


class CheckSpecie(BaseTestCase, TestCase):
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

    @classmethod
    def tearDownClass(cls):
        # truncate cryoweb database after loading
        if db_has_data():
            truncate_database()

        # calling my base class teardown class
        super().tearDownClass()

    def test_check_species(self):
        """Testing species and synonims"""

        self.assertTrue(check_species("Germany"))

        # now delete a synonim
        synonim = SpecieSynonim.objects.get(
            language__label='Germany',
            word='Cattle')
        synonim.delete()

        self.assertFalse(check_species("Germany"))


class UploadCryoweb(BaseTestCase, TestCase):
    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission
        self.submission = Submission.objects.get(pk=1)

    def tearDown(self):
        """Clean test database after modifications"""

        # truncate cryoweb database after loading
        if db_has_data():
            truncate_database()

        # calling my base class teardown class
        super().tearDown()

    def test_database_name(self):
        self.assertEqual(
            settings.DATABASES['cryoweb']['NAME'], 'test_cryoweb')

    def test_upload_cryoweb(self):
        """Testing uploading and uploading with data into cryoweb"""

        self.assertTrue(upload_cryoweb(self.submission.id))
        self.assertTrue(db_has_data())

        # if I try again to upload cryoweb, I will get a False object and
        # submission message
        self.assertRaises(
            CryoWebImportError,
            upload_cryoweb,
            self.submission.id)

        # reload submission
        self.submission = Submission.objects.get(pk=1)

        self.assertEqual(
            self.submission.status,
            Submission.STATUSES.get_value('error'))

        self.assertIn(
            "Cryoweb has data",
            self.submission.message)

    # mock subprocess.run an raise Exception. Read it and update submission
    # message using helpers.upload_cryoweb
    def test_upload_cryoweb_errors(self):
        """Testing errors in uploading cryoweb data"""

        with patch('subprocess.run') as runMock:
            runMock.side_effect = Exception("Test upload failed")
            self.assertFalse(upload_cryoweb(self.submission.id))

            # reload submission
            self.submission = Submission.objects.get(pk=1)

            self.assertEqual(
                self.submission.status,
                Submission.STATUSES.get_value('error'))

            self.assertIn(
                "Test upload failed",
                self.submission.message)


class CryowebImport(BaseTestCase, TestCase):
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

    @classmethod
    def tearDownClass(cls):
        # truncate cryoweb database after loading
        if db_has_data():
            truncate_database()

        # calling my base class teardown class
        super().tearDownClass()

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission
        self.submission = Submission.objects.get(pk=1)

    def test_database_name(self):
        self.assertEqual(
            settings.DATABASES['cryoweb']['NAME'], 'test_cryoweb')

    def test_cryoweb_import(self):
        """Import from cryoweb staging database into UID"""

        self.assertTrue(cryoweb_import(self.submission))

        # check breed upload
        queryset = DictBreed.objects.all()
        breeds = [dictbreed.supplied_breed for dictbreed in queryset]

        self.assertEqual(len(queryset), 2)
        self.assertListEqual(
            breeds, ['Aberdeen Angus', 'Ostfriesisches Milchschaf'],
            msg="Check breeds loaded")

        # check name upload (5 animal, 1 sample)
        queryset = Name.objects.filter(submission=self.submission)
        self.assertEqual(len(queryset), 6, msg='check name load')

        # check animal name
        queryset = Animal.objects.all()
        self.assertEqual(len(queryset), 3, msg="check animal load")

        queryset = Sample.objects.all()
        self.assertEqual(len(queryset), 1, msg="check sample load")
