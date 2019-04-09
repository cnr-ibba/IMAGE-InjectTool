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
from image_app.models import (
    Submission, db_has_data, DictSpecie, DictSex, DictBreed, Name, Animal,
    Sample, DictUberon, DictCountry)

from ..helpers import (
    logger, CRBAnimReader, upload_crbanim, fill_uid_breed, fill_uid_names,
    fill_uid_animal, fill_uid_sample)
from .common import BaseTestCase


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

    def test_check_species(self):
        """Test check species method"""

        # get a country
        country = DictCountry.objects.get(label="United Kingdom")

        check, not_found = self.reader.check_species(country)

        self.assertTrue(check)
        self.assertEqual(len(not_found), 0)

        # changing species set
        DictSpecie.objects.filter(label='Bos taurus').delete()

        check, not_found = self.reader.check_species(country)

        # the read species are not included in fixtures
        self.assertFalse(check)
        self.assertGreater(len(not_found), 0)

    def test_check_sex(self):
        """Test check sex method"""

        check, not_found = self.reader.check_sex()

        self.assertTrue(check)
        self.assertEqual(len(not_found), 0)

        # changing sex set
        DictSex.objects.filter(label='female').delete()

        check, not_found = self.reader.check_sex()

        # the read species are not included in fixtures
        self.assertFalse(check)
        self.assertGreater(len(not_found), 0)

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
        # record are all Female. No record after filtering case sensitive
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

        self.assertEqual(len(data), 3)

        # No record after filtering male case insensitive
        data = self.reader.filter_by_column_values(
            "sex",
            ['male'],
            ignorecase=True)
        data = list(data)

        self.assertEqual(len(data), 0)


class ProcessRecordTestCase(BaseTestCase, TestCase):
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


class UploadCRBAnimTestCase(BaseTestCase, TestCase):

    def test_upload_crbanim(self):
        """Testing uploading and importing data from crbanim to UID"""

        self.assertTrue(upload_crbanim(self.submission))

        # reload submission
        self.submission.refresh_from_db()

        # assert submission messages
        self.assertEqual(
            self.submission.status,
            LOADED)

        self.assertIn(
            "CRBAnim import completed for submission",
            self.submission.message)

        # assert data into database
        self.assertTrue(db_has_data())
        self.assertTrue(Animal.objects.exists())
        self.assertTrue(Sample.objects.exists())

    @patch("crbanim.helpers.CRBAnimReader.check_species",
           return_value=[False, 'Rainbow trout'])
    def test_upload_crbanim_errors(self, my_check):
        """Testing importing with data into UID with errors"""

        self.assertFalse(upload_crbanim(self.submission))

        # reload submission
        self.submission.refresh_from_db()

        # test my mock method called
        self.assertTrue(my_check.called)

        # reload submission
        self.submission = Submission.objects.get(pk=1)

        self.assertEqual(
            self.submission.status,
            ERROR)

        self.assertIn(
            "Some species are not loaded in UID database",
            self.submission.message)

        # assert data into database
        self.assertFalse(db_has_data())
        self.assertFalse(Animal.objects.exists())
        self.assertFalse(Sample.objects.exists())

    @patch("crbanim.helpers.CRBAnimReader.check_sex",
           return_value=[False, 'unknown'])
    def test_upload_crbanim_errors_with_sex(self, my_check):
        """Testing importing with data into UID with errors"""

        self.assertFalse(upload_crbanim(self.submission))

        # reload submission
        self.submission.refresh_from_db()

        # test my mock method called
        self.assertTrue(my_check.called)

        # reload submission
        self.submission = Submission.objects.get(pk=1)

        self.assertEqual(
            self.submission.status,
            ERROR)

        # check for two distinct messages
        self.assertIn(
            "Not all Sex terms are loaded into database",
            self.submission.message)

        self.assertNotIn(
            "CRBAnim import completed for submission",
            self.submission.message)

        # assert data into database
        self.assertFalse(db_has_data())
        self.assertFalse(Animal.objects.exists())
        self.assertFalse(Sample.objects.exists())
