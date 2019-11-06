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
from common.tests import WebSocketMixin
from language.models import SpecieSynonym
from uid.models import (
    Submission, DictBreed, Animal, Sample, DictSex,
    DictCountry, DictSpecie)
from uid.tests import DataSourceMixinTestCase

from ..helpers import (
    upload_cryoweb, check_species, CryoWebImportError, cryoweb_import,
    check_UID, check_countries)
from ..models import db_has_data, truncate_database, BreedsSpecies


class BaseMixin():
    # import this file and populate database once
    fixtures = [
        'cryoweb/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/organization',
        'uid/submission',
        'uid/user',
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


class ImportMixin(WebSocketMixin, CryoWebMixin):
    """Mixing to test cryoweb_import method"""

    def test_cryoweb_import(self):
        """A method to test if data were imported from cryoweb or not"""

        self.assertTrue(cryoweb_import(self.submission))

        # check breed upload
        queryset = DictBreed.objects.all()

        breeds = [(dictbreed.supplied_breed, dictbreed.country.label)
                  for dictbreed in queryset]

        self.assertEqual(len(queryset), 4)
        self.assertListEqual(
            breeds, [
                ('Bunte Bentheimer', 'United Kingdom'),
                ('Ostfriesisches Milchschaf', 'Italy'),
                ('Aberdeen Angus', 'Germany'),
                ('Ostfriesisches Milchschaf', 'Germany')],
            msg="Check breeds loaded")

        # check animal name
        queryset = Animal.objects.all()
        self.assertEqual(len(queryset), 3, msg="check animal load")

        queryset = Sample.objects.all()
        self.assertEqual(len(queryset), 1, msg="check sample load")

        # check async message called
        message = 'Loaded'
        notification_message = (
            'Cryoweb import completed for submission: 1')
        validation_message = {
            'animals': 3, 'samples': 1,
            'animal_unkn': 3, 'sample_unkn': 1,
            'animal_issues': 0, 'sample_issues': 0}

        self.check_message(message, notification_message, validation_message)


class CheckSpecie(CryoWebMixin, BaseMixin, TestCase):
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


class CheckCountry(CryoWebMixin, BaseMixin, TestCase):
    def test_check_country(self):
        """Test that all Cryoweb countries are defined in database"""

        countries_not_found = check_countries()

        self.assertEqual(countries_not_found, [])

        # remove a country from UID
        DictCountry.objects.filter(label="Germany").delete()

        countries_not_found = check_countries()

        self.assertEqual(countries_not_found, ['Germany'])


class CheckBreed(TestCase):
    # import this file and populate database once
    fixtures = [
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/organization',
        'uid/submission',
        'uid/user',
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


class CheckUIDTest(CryoWebMixin, BaseMixin, TestCase):
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

    def test_missing_country(self):
        # remove a country from UID
        DictCountry.objects.filter(label="Germany").delete()

        self.assertRaisesRegex(
            CryoWebImportError,
            "Not all countries are loaded into database:",
            check_UID, self.submission)

    def test_check_UID(self):
        """testing normal behaviour"""

        self.assertTrue(check_UID(self.submission))


class UploadCryoweb(
        WebSocketMixin, DataSourceMixinTestCase, BaseMixin, TestCase):
    """Test upload cryoweb dump into cryoweb database"""

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

        # check async message called
        message = 'Error'
        notification_message = 'Error in importing data: Cryoweb has data'

        self.check_message(message, notification_message)

    # mock subprocess.run and raise Exception. Read it and update submission
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

            # check async message called
            message = 'Error'
            notification_message = ('Error in importing data: Test '
                                    'upload failed')

            self.check_message(message, notification_message)


class CryowebImport(ImportMixin, BaseMixin, TestCase):
    def test_database_name(self):
        self.assertEqual(
            settings.DATABASES['cryoweb']['NAME'], 'test_cryoweb')

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

        # check async message called
        message = 'Error'
        notification_message = (
            'Error in importing data: Test message')

        self.check_message(message, notification_message)


class CryowebReload(ImportMixin, BaseMixin, TestCase):
    """Simulate a cryoweb reload case. Load data as in CryowebImport, then
    call test which reload the same data"""

    # override fixtures
    fixtures = [
        'cryoweb/auth',
        'cryoweb/dictbreed',
        'cryoweb/uid',
        'language/dictspecie',
        'language/speciesynonym'
    ]


class CryowebUpdate(ImportMixin, BaseMixin, TestCase):
    """Simulate a cryoweb update with the same dataset. Data already
    present will be ignored"""

    # override fixtures
    fixtures = [
        'cryoweb/auth',
        'cryoweb/dictbreed',
        'cryoweb/uid',
        'language/dictspecie',
        'language/speciesynonym'
    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track old submission
        self.old_submission = Submission.objects.get(pk=1)

        # generate a new submission from old submission object
        submission = self.submission
        submission.pk = None
        submission.title = "Updated database"
        submission.datasource_version = "Updated database"
        submission.save()

        # track the new submission
        self.submission = submission

        # now delete an animal and its associated sample
        sample = Sample.objects.get(pk=1)
        animal = sample.animal
        animal.delete()

    # override ImportMixin.test_cryoweb_import
    def test_cryoweb_import(self):
        """A method to test if data were imported from cryoweb or not"""

        self.assertTrue(cryoweb_import(self.submission))

        # check breed upload
        queryset = DictBreed.objects.all()

        breeds = [(dictbreed.supplied_breed, dictbreed.country.label)
                  for dictbreed in queryset]

        self.assertEqual(len(queryset), 4)
        self.assertListEqual(
            breeds, [
                ('Bunte Bentheimer', 'United Kingdom'),
                ('Ostfriesisches Milchschaf', 'Italy'),
                ('Aberdeen Angus', 'Germany'),
                ('Ostfriesisches Milchschaf', 'Germany')],
            msg="Check breeds loaded")

        # check animal and samples
        queryset = Animal.objects.all()
        self.assertEqual(len(queryset), 3, msg="check animal load")

        queryset = Sample.objects.all()
        self.assertEqual(len(queryset), 1, msg="check sample load")

        # assert data are in the proper submission
        self.assertEqual(self.old_submission.animal_set.count(), 2)
        self.assertEqual(self.old_submission.sample_set.count(), 0)

        self.assertEqual(self.submission.animal_set.count(), 1)
        self.assertEqual(self.submission.sample_set.count(), 1)

        # check async message called
        message = 'Loaded'
        notification_message = (
            'Cryoweb import completed for submission: 2')
        validation_message = {
            'animals': 1, 'samples': 1,
            'animal_unkn': 1, 'sample_unkn': 1,
            'animal_issues': 0, 'sample_issues': 0}

        self.check_message(
            message,
            notification_message,
            validation_message,
            pk=self.submission.id)
