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

from common.constants import ERROR
from language.models import SpecieSynonym
from image_app.models import (
    Submission, DictBreed, Name, Animal, Sample, DictSex,
    DictCountry, DictSpecie)
from common.tests import DataSourceMixinTestCase

from ..helpers import (
    upload_cryoweb, check_species, CryoWebImportError, cryoweb_import,
    check_UID)
from ..models import db_has_data, truncate_database, BreedsSpecies


class BaseTestCase():
    # import this file and populate database once
    fixtures = [
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/organization',
        'image_app/submission',
        'image_app/user',
        'language/dictspecie',
        'language/speciesynonym'
    ]

    # By default, fixtures are only loaded into the default database. If you
    # are using multiple databases and set multi_db=True, fixtures will be
    # loaded into all databases. However, this will raise problems when
    # managing extended user models
    multi_db = False

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission
        self.submission = Submission.objects.get(pk=1)


class CryoWebMixin(object):
    """Custom methods to upload cryoweb data into database for testing"""

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


class CheckSpecie(CryoWebMixin, BaseTestCase, TestCase):
    def test_check_species(self):
        """Testing species and synonyms"""

        united_kingdom = DictCountry.objects.get(label="United Kingdom")

        # test for species synonoms for cryoweb
        self.assertTrue(check_species(united_kingdom))

        # now delete a synonym
        synonym = SpecieSynonym.objects.get(
            language__label='United Kingdom',
            word='Cattle')
        synonym.delete()

        self.assertFalse(check_species(united_kingdom))

    def test_no_species(self):
        """Test no species in cryoweb database"""

        queryset = BreedsSpecies.objects.all()
        queryset.delete()

        self.assertRaisesRegex(
            CryoWebImportError,
            "You have no species",
            check_species, "United Kingdom")


class CheckBreed(TestCase):
    # import this file and populate database once
    fixtures = [
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/organization',
        'image_app/submission',
        'image_app/user',
    ]

    def test_add_breed(self):
        italy = DictCountry.objects.get(label="Italy")
        united_kingdom = DictCountry.objects.get(label="United Kingdom")

        sus = DictSpecie.objects.get(label="Sus scrofa")

        # inserting an already present breed get the object without creation
        breed, created = DictBreed.objects.get_or_create(
            supplied_breed="Bunte Bentheimer",
            specie=sus,
            country=united_kingdom)

        self.assertFalse(created)

        # inserting a breed in a different country add a record
        breed, created = DictBreed.objects.get_or_create(
            supplied_breed="Bunte Bentheimer",
            specie=sus,
            country=italy)

        self.assertTrue(created)


class CheckUIDTest(CryoWebMixin, BaseTestCase, TestCase):
    def test_empty_dictsex(self):
        """Empty dictsex and check that I can't proceed"""

        queryset = DictSex.objects.all()
        queryset.delete()

        self.assertRaisesRegex(
            CryoWebImportError,
            "You have to upload DictSex data",
            check_UID, self.submission)

    def test_no_synonym(self):
        # now delete a synonym
        synonym = SpecieSynonym.objects.get(
            language__label='United Kingdom',
            word='Cattle')
        synonym.delete()

        self.assertRaisesRegex(
            CryoWebImportError,
            "Some species haven't a synonym!",
            check_UID, self.submission)

    def test_check_UID(self):
        """testing normal behaviour"""

        self.assertTrue(check_UID(self.submission))


class UploadCryoweb(DataSourceMixinTestCase, BaseTestCase, TestCase):
    # define attribute in DataSourceMixinTestCase
    model = Submission

    # need to clean database after testing import. Can't use CryowebMixin
    # since i need to test cryoweb import
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
        """Testing uploading and importing data from cryoweb to UID"""

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
            ERROR)

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
                ERROR)

            self.assertIn(
                "Test upload failed",
                self.submission.message)


class CryowebImport(CryoWebMixin, BaseTestCase, TestCase):
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

    @patch("cryoweb.helpers.check_UID", side_effect=Exception("Test message"))
    def test_cryoweb_import_errors(self, my_check):
        """Testing importing with data into UID with errors"""

        self.assertFalse(cryoweb_import(self.submission))
        self.assertTrue(my_check.called)

        # reload submission
        self.submission = Submission.objects.get(pk=1)

        self.assertEqual(
            self.submission.status,
            ERROR)

        self.assertIn(
            "Test message",
            self.submission.message)
