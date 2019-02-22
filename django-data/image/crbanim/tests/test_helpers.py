#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 15:49:18 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging
from unittest.mock import patch

from django.test import TestCase

from common.constants import ERROR, LOADED
from common.tests import DataSourceMixinTestCase
from image_app.models import Submission, db_has_data, DictSpecie, DictSex

from ..helpers import (
    logger, CRBAnimReader, upload_crbanim, CRBAnimImportError)


class BaseTestCase(DataSourceMixinTestCase):
    # define attribute in DataSourceMixinTestCase
    model = Submission

    # import this file and populate database once
    fixtures = [
        'crbanim/dictspecie',
        'crbanim/submission',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/organization',
        'image_app/user'
    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission
        self.submission = Submission.objects.get(pk=1)


class CRBAnimReaderTestCase(BaseTestCase, TestCase):
    def setUp(self):
        # calling my base class setup
        super().setUp()

        # crate a CRBAnimReade object
        self.reader = CRBAnimReader()

        # get filenames for DataSourceMixinTestCase.dst_path
        self.reader.read_file(self.dst_path)

    def test_has_columns(self):
        """Test if class has columns"""

        reference = [
            'BRC_identifier',
            'BRC_name',
            'associated_research_project_name',
            'BRC_responsible_last_name',
            'BRC_responsible_first_name',
            'BRC_contact_email',
            'organization_name',
            'organisation_adress',
            'organization_url',
            'organization_country',
            'BRC_address',
            'BRC_url',
            'BRC_country',
            'sample_identifier',
            'EBI_Biosample_identifier',
            'animal_ID',
            'sex',
            'species_latin_name',
            'NCBI_taxo_id',
            'breed_name',
            'country_of_origin',
            'sampling_protocol_url',
            'sampling_date',
            'sample_type_name',
            'sample_type_identifier',
            'sample_type_ontology',
            'body_part_name',
            'body_part_identifier',
            'body_part_ontology',
            'animal_birth_date',
            'sample_storage_temperature',
            'sample_container_type',
            'sample_fixer_nature']

        self.assertEqual(reference, self.reader.header)

    def test_debug_row(self):
        """Assert a function is callable"""

        self.assertLogs(logger=logger, level=logging.DEBUG)

    def test_check_species(self):
        """Test check species method"""

        self.assertTrue(self.reader.check_species())

        # changing species set
        DictSpecie.objects.filter(label='Bos taurus').delete()

        # the read species are not included in fixtures
        self.assertFalse(self.reader.check_species())

    def test_check_sex(self):
        """Test check sex method"""

        self.assertTrue(self.reader.check_sex())

        # changing sex set
        DictSex.objects.filter(label='female').delete()

        # the read species are not included in fixtures
        self.assertFalse(self.reader.check_sex())


class UploadCRBAnimTestCase(BaseTestCase, TestCase):

    def test_upload_crbanim(self):
        """Testing uploading and importing data from crbanim to UID"""

        self.assertTrue(upload_crbanim(self.submission))

        # assert submission messages
        self.assertEqual(
            self.submission.status,
            LOADED)

        self.assertIn(
            "CRBAnim import completed for submission",
            self.submission.message)

        # assert data into database
        self.assertTrue(db_has_data())

    @patch("crbanim.helpers.CRBAnimReader.check_species",
           side_effect=Exception("Test message"))
    def test_upload_crbanim_errors(self, my_check):
        """Testing importing with data into UID with errors"""

        self.assertFalse(upload_crbanim(self.submission))
        self.assertTrue(my_check.called)

        # reload submission
        self.submission = Submission.objects.get(pk=1)

        self.assertEqual(
            self.submission.status,
            ERROR)

        self.assertIn(
            "Test message",
            self.submission.message)

        # assert data into database
        self.assertFalse(db_has_data())
