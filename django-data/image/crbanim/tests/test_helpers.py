#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 15:49:18 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import logging

from unittest.mock import patch
from collections import namedtuple

from django.test import TestCase

from common.tests import WebSocketMixin
from uid.models import (
    DictSex, DictBreed, Name, Animal,
    Sample, DictUberon, DictCountry)
from uid.tests.mixins import (
    DataSourceMixinTestCase, FileReaderMixinTestCase)

from ..helpers import (
    logger, CRBAnimReader, upload_crbanim, fill_uid_breed, fill_uid_names,
    fill_uid_animal, fill_uid_sample, find_storage_type, sanitize_url)
from .common import BaseTestCase


class CRBAnimMixin(DataSourceMixinTestCase, WebSocketMixin):
    """Common test for CRBanim classes"""

    # define the method to upload data from. Since the function is now inside
    # a class it becomes a method, specifically a bound method and is supposed
    # to receive the self attribute by default. If we don't want to get the
    # self attribute, we have to declare function as a staticmetho
    # https://stackoverflow.com/a/35322635/4385116
    upload_method = staticmethod(upload_crbanim)

    def test_upload_crbanim(self):
        """Testing uploading and importing data from crbanim to UID"""

        # test data loaded
        message = "CRBAnim import completed for submission"
        self.upload_datasource(message)

        # check async message called
        notification_message = (
            'CRBAnim import completed for submission: 1')
        validation_message = {
            'animals': 1, 'samples': 2,
            'animal_unkn': 1, 'sample_unkn': 2,
            'animal_issues': 0, 'sample_issues': 0}

        # check async message called using WebSocketMixin.check_message
        self.check_message('Loaded', notification_message, validation_message)

    def check_errors(self, my_check, message, notification_message):
        """Common stuff for error in crbanim loading"""

        super().check_errors(my_check, message)

        # check async message called using WebSocketMixin.check_message
        self.check_message('Error', notification_message)


class CRBAnimReaderTestCase(
        FileReaderMixinTestCase, DataSourceMixinTestCase, BaseTestCase,
        TestCase):
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
            'sample_availability',
            'sample_bibliographic_references',
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

        self.reader.print_line(0)
        self.assertLogs(logger=logger, level=logging.DEBUG)

    def test_filter_by_column(self):
        """Filter records by column value"""

        # filter out biosample records from mydata
        data = self.reader.filter_by_column_values(
            "EBI_Biosample_identifier",
            [None])
        data = list(data)

        self.assertEqual(len(data), 2)

    def test_filter_by_column_case(self):
        """Filter records by column value case insensitive"""

        # filter out biosample records from mydata
        # record have capital letter. No record after filtering case sensitive
        data = self.reader.filter_by_column_values(
            "sex",
            ['female'],
            ignorecase=False)
        data = list(data)

        self.assertEqual(len(data), 0)

        # filtering female case insensitive
        data = self.reader.filter_by_column_values(
            "sex",
            ['female'],
            ignorecase=True)
        data = list(data)

        self.assertEqual(len(data), 1)

        # No record after filtering foo case insensitive
        data = self.reader.filter_by_column_values(
            "sex",
            ['foo'],
            ignorecase=True)
        data = list(data)

        self.assertEqual(len(data), 0)

    def test_is_valid(self):
        """Test recognizing a good CRBanim file"""

        with open(self.dst_path) as handle:
            chunk = handle.read(2048)

        check, not_found = self.reader.is_valid(chunk)

        # a good crbanim file returns True and an empty list
        self.assertTrue(check)
        self.assertEqual(not_found, [])

        # assert a not good file. self.base_dir comes from
        # common.tests.mixins.DataSourceMixinTestCase
        filename = os.path.join(
            self.base_dir,
            "Mapping_rules_CRB-Anim_InjectTool_v1.csv")

        with open(filename) as handle:
            chunk = handle.read(2048)

        check, not_found = self.reader.is_valid(chunk)

        # a invalid crbanim file returns False and a list
        self.assertFalse(check)
        self.assertGreater(len(not_found), 0)


class ProcessRecordTestCase(DataSourceMixinTestCase, BaseTestCase, TestCase):
    """A class to test function which process record"""

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # crate a CRBAnimReade object
        self.reader = CRBAnimReader()

        # get filenames for DataSourceMixinTestCase.dst_path
        self.reader.read_file(self.dst_path)

        # filter out biosample records from mydata
        data = self.reader.filter_by_column_values(
            "EBI_Biosample_identifier",
            [None])
        self.data = list(data)

        # track the sample record for test
        self.record = self.data[0]

        # set a country
        self.country = DictCountry.objects.get(label="United Kingdom")

        # fill object to test inserts. Fill breed
        self.breed = fill_uid_breed(self.record, self.country)

        # fill names
        self.animal_name, self.sample_name = fill_uid_names(
            self.record, self.submission)

        # filling animal and samples
        self.animal = fill_uid_animal(
            self.record,
            self.animal_name,
            self.breed,
            self.submission,
            {})

        # testing samples
        self.sample = fill_uid_sample(
            self.record,
            self.sample_name,
            self.animal,
            self.submission)

    def test_fill_uid_breed(self):
        """testing fill_uid_breed"""

        # testing output
        self.assertIsInstance(self.breed, DictBreed)
        self.assertEqual(self.breed.supplied_breed, self.record.breed_name)
        self.assertEqual(
            self.breed.specie.label, self.record.species_latin_name)

    def test_fill_uid_names(self):
        # testing output
        self.assertIsInstance(self.animal_name, Name)
        self.assertIsInstance(self.sample_name, Name)

        self.assertEqual(self.animal_name.name, self.record.animal_ID)
        self.assertEqual(self.sample_name.name, self.record.sample_identifier)

    def test_fill_uid_animals(self):
        # testing animal
        self.assertIsInstance(self.animal, Animal)

        # testing animal attributes
        sex = DictSex.objects.get(label__iexact=self.record.sex)
        self.assertEqual(self.animal.sex, sex)

    def test_fill_uid_samples(self):
        # testing sample
        self.assertIsInstance(self.sample, Sample)

        # testing sample attributes
        organism_part = DictUberon.objects.get(
            label__iexact="bone marrow")
        self.assertEqual(self.sample.organism_part, organism_part)

    def test_organism_part(self):
        """Check that an 'unknown' organims_part generate a DictUberon
        relying on sample_type_name (see crbanim_test_data.csv file)"""

        # get a new record
        record = self.data[1]

        # fill breeds
        breed = fill_uid_breed(record, self.country)

        # creating name
        animal_name, sample_name = fill_uid_names(
            record, self.submission)

        # filling animal and samples
        animal = fill_uid_animal(
            record,
            animal_name,
            breed,
            self.submission,
            {})

        # testing samples
        sample = fill_uid_sample(
            record,
            sample_name,
            animal,
            self.submission)

        # testing sample attributes
        organism_part = DictUberon.objects.get(
            label__iexact="uterus")
        self.assertEqual(sample.organism_part, organism_part)

    def test_find_storage_type(self):
        """Asserting storage type conversion"""

        result = find_storage_type(self.record)
        self.assertEqual(result, 2)

        # create a fare record object
        Data = namedtuple("Data", ["sample_storage_temperature"])
        record = Data._make(["meow"])

        result = find_storage_type(record)
        self.assertIsNone(result)


class UploadCRBAnimTestCase(CRBAnimMixin, BaseTestCase, TestCase):

    @patch("crbanim.helpers.CRBAnimReader.check_species",
           return_value=[False, 'Rainbow trout'])
    def test_upload_crbanim_errors_with_species(self, my_check):
        """Testing importing with data into UID with errors"""

        message = "Some species are not loaded in UID database"
        notification_message = (
            "Error in importing data: Some species "
            "are not loaded in UID database: check for 'Rainbow "
            "trout' in your dataset")

        # check crbanim import fails
        self.check_errors(my_check, message, notification_message)

    @patch("crbanim.helpers.CRBAnimReader.check_sex",
           return_value=[False, 'unknown'])
    def test_upload_crbanim_errors_with_sex(self, my_check):
        """Testing importing with data into UID with errors"""

        message = "Not all Sex terms are loaded into database"
        notification_message = (
            "Error in importing data: %s: check "
            "for 'unknown' in your dataset" % (message))

        # check crbanim import fails
        self.check_errors(my_check, message, notification_message)

    @patch("crbanim.helpers.CRBAnimReader.check_countries",
           return_value=[False, 'unknown'])
    def test_upload_crbanim_errors_with_countries(self, my_check):
        """Testing importing with data into UID with errors"""

        message = "Not all countries are loaded into database"
        notification_message = (
            "Error in importing data: %s: check "
            "for 'unknown' in your dataset" % (message))

        # check crbanim import fails
        self.check_errors(my_check, message, notification_message)


class ReloadCRBAnimTestCase(CRBAnimMixin, BaseTestCase, TestCase):

    """Simulate a crbanim reload case. Load data as in
    UploadCRBAnimTestCase, then call test which reload the same data"""

    # override used fixtures
    fixtures = [
        'crbanim/auth',
        'crbanim/dictspecie',
        'crbanim/uid',
        'crbanim/submission',
        'language/speciesynonym'
    ]


class SanitizeAccessionTest(TestCase):

    def setUp(self):
        self.queries = [
            (
                ("https://crb-anim.fr/access-to-collection/#/simplesearch?"
                 "SAMPLEIDENTIFIER=Ovar-Mér-3796-1"),
                ("https://crb-anim.fr/access-to-collection/#/simplesearch?"
                 "SAMPLEIDENTIFIER=Ovar-M%C3%A9r-3796-1")
            ),
        ]

    def test_sanitize_accession(self):
        for query in self.queries:
            url, reference = query
            test = sanitize_url(url)
            self.assertEqual(reference, test)
