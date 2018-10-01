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
from image_app.models import Submission, DictBreed, Name, Animal

from .test_cryoweb import BaseTestCase
from ..helpers import (
    upload_cryoweb, check_species, CryoWebImportError, cryoweb_import,
    fill_uid_breeds, fill_uid_names, fill_uid_animals)
from ..models import db_has_data, truncate_database


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

    def test_fill_uid_breeds(self):
        # call function
        fill_uid_breeds(self.submission)

        # eval queryset
        queryset = DictBreed.objects.all()
        breeds = [dictbreed.supplied_breed for dictbreed in queryset]

        self.assertEqual(len(queryset), 2)
        self.assertListEqual(
            breeds, ['Aberdeen Angus', 'Ostfriesisches Milchschaf'])

    def test_fill_uid_names(self):
        # call function
        fill_uid_names(self.submission)

        queryset = Name.objects.filter(submission=self.submission)

        self.assertEqual(len(queryset), 5)

    def test_fill_uid_animals(self):
        # call function
        fill_uid_breeds(self.submission)
        fill_uid_names(self.submission)
        fill_uid_animals(self.submission)

        queryset = Animal.objects.all()

        self.assertEqual(len(queryset), 3)

    @patch('cryoweb.helpers.fill_uid_animals')
    @patch('cryoweb.helpers.fill_uid_names')
    @patch('cryoweb.helpers.fill_uid_breeds')
    def test_cryoweb_import(self, my_breeds, my_names, my_animals):
        """Import from cryoweb staging database into UID"""

        self.assertTrue(cryoweb_import(self.submission))
        self.assertTrue(my_breeds.called)
        self.assertTrue(my_names.called)
        self.assertTrue(my_animals.called)
