#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 10:58:42 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import types
from collections import defaultdict
from unittest.mock import patch, Mock

from django.test import TestCase
from django.core.management import call_command

from common.tests import WebSocketMixin
from image_app.tests.mixins import (
    DataSourceMixinTestCase, FileReaderMixinTestCase)

from ..helpers import ExcelTemplateReader, upload_template, TEMPLATE_COLUMNS
from .common import BaseExcelMixin


class ExcelTemplateReaderTestCase(
        FileReaderMixinTestCase, DataSourceMixinTestCase, BaseExcelMixin,
        TestCase):
    """Test excel class upload"""

    def setUp(self):
        # calling my base class setup
        super().setUp()

        self.maxDiff = None

        # crate a Excel Template object
        self.reader = ExcelTemplateReader()

        # get filenames for DataSourceMixinTestCase.dst_path
        self.reader.read_file(self.dst_path)

    def test_check_sheets(self):
        # test check sheets method
        status, not_found = self.reader.check_sheets()

        self.assertTrue(status)
        self.assertEqual(not_found, [])

        # override sheet names
        self.reader.sheet_names = []

        # check method
        status, not_found = self.reader.check_sheets()

        self.assertFalse(status)
        self.assertEqual(not_found, ['breed', 'animal', 'sample'])

    def test_check_columns(self):
        # test check sheets method
        status, not_found = self.reader.check_columns()

        self.assertTrue(status)
        self.assertIsInstance(not_found, defaultdict)
        self.assertEqual(len(not_found), 0)

    @patch('xlrd.open_workbook')
    def test_check_columns_issue(self, mock_open):
        """Test a file with columns issues"""

        # creating a mock excel book
        mock_book = Mock()

        # customizing the mock object
        mock_book.sheet_names.return_value = ['breed', 'animal', 'sample']

        # creating a mock sheet for breed
        breed_sheet = Mock()
        breed_sheet.nrows = 1

        # now setting rows to a fake sheet
        breed_sheet.row_values.return_value = []

        # creating a mock sheet for animal
        animal_sheet = Mock()
        animal_sheet.nrows = 1

        # now setting rows to a fake sheet
        animal_sheet.row_values.return_value = []

        # creating a mock sheet for sample
        sample_sheet = Mock()
        sample_sheet.nrows = 1

        # now setting rows to a fake sheet
        sample_sheet.row_values.return_value = []

        # finally setting sheet to the fabe excel object
        mock_book.sheet_by_name.side_effect = [
            breed_sheet, animal_sheet, sample_sheet]

        # returning the mock object when opening a workbook
        mock_open.return_value = mock_book

        # now calling methods
        reader = ExcelTemplateReader()
        reader.read_file("fake file")

        # create the reference error output
        reference = defaultdict(list)
        reference['breed'] += TEMPLATE_COLUMNS['breed']
        reference['animal'] += TEMPLATE_COLUMNS['animal']
        reference['sample'] += TEMPLATE_COLUMNS['sample']

        status, test = reader.check_columns()

        self.assertFalse(status)
        self.assertIsInstance(test, defaultdict)
        self.assertDictEqual(reference, test)

    def check_generator(self, records, length):
        self.assertIsInstance(records, types.GeneratorType)
        self.assertEqual(len(list(records)), length)

    def test_get_breed_records(self):
        """get_breed_records returns an iterator"""

        breeds = self.reader.get_breed_records()
        self.check_generator(breeds, 2)

    def test_get_animal_records(self):
        """get_animal_records returns an iterator"""

        animals = self.reader.get_animal_records()
        self.check_generator(animals, 3)

    def test_get_sample_records(self):
        """get_sample_records returns an iterator"""

        samples = self.reader.get_sample_records()
        self.check_generator(samples, 3)

    def test_check_accuracies(self):
        """Test check accuracies method"""

        check, not_found = self.reader.check_accuracies()

        self.assertTrue(check)
        self.assertEqual(len(not_found), 0)

    @patch('xlrd.open_workbook')
    def test_check_accuracies_issue(self, mock_open):
        """Checking issues with accuracy in excels data"""

        # creating a mock excel book
        mock_book = Mock()

        # customizing the mock object
        mock_book.sheet_names.return_value = ['breed', 'animal', 'sample']

        # creating a mock sheet for animal
        animal_sheet = Mock()
        animal_sheet.nrows = 2

        # creating a fake row of data
        fake_row = ["" for col in TEMPLATE_COLUMNS['animal']]

        # get birth location accuracy index
        accuracy_idx = TEMPLATE_COLUMNS['animal'].index(
            "Birth location accuracy")

        # set a fake accuracy item
        fake_row[accuracy_idx] = "Fake"

        # now setting rows to a fake sheet
        animal_sheet.row_values.side_effect = [
            TEMPLATE_COLUMNS['animal'],
            fake_row]

        # creating a mock sheet for sample
        sample_sheet = Mock()
        sample_sheet.nrows = 2

        # creating a fake row of data
        fake_row = ["" for col in TEMPLATE_COLUMNS['sample']]

        # get birth location accuracy index
        accuracy_idx = TEMPLATE_COLUMNS['sample'].index(
            "Collection place accuracy")

        # set a fake accuracy item
        fake_row[accuracy_idx] = "Fake"

        # now setting rows to a fake sheet
        sample_sheet.row_values.side_effect = [
            TEMPLATE_COLUMNS['sample'],
            fake_row]

        # finally setting sheet to the fabe excel object
        mock_book.sheet_by_name.side_effect = [animal_sheet, sample_sheet]

        # returning the mock object when opening a workbook
        mock_open.return_value = mock_book

        # now calling methods
        reader = ExcelTemplateReader()
        reader.read_file("fake file")

        # define the expected value
        reference = (False, set(["Fake"]))
        test = reader.check_accuracies()

        self.assertEqual(reference, test)


class ExcelMixin(DataSourceMixinTestCase, WebSocketMixin, BaseExcelMixin):
    """Common tests for Excel classes"""

    # define the method to upload data from. Since the function is now inside
    # a class it becomes a method, specifically a bound method and is supposed
    # to receive the self attribute by default. If we don't want to get the
    # self attribute, we have to declare function as a staticmetho
    # https://stackoverflow.com/a/35322635/4385116
    upload_method = staticmethod(upload_template)

    def test_upload_template(self):
        """Testing uploading and importing data from excel template to UID"""

        # test data loaded
        message = "Template import completed for submission"
        self.upload_datasource(message)

        # check async message called
        notification_message = (
            'Template import completed for submission: 1')
        validation_message = {
            'animals': 3, 'samples': 3,
            'animal_unkn': 3, 'sample_unkn': 3,
            'animal_issues': 0, 'sample_issues': 0}

        # check async message called using WebSocketMixin.check_message
        self.check_message('Loaded', notification_message, validation_message)

    def check_errors(self, my_check, message, notification_message):
        """Common stuff for error in excel template loading"""

        super().check_errors(my_check, message)

        # check async message called using WebSocketMixin.check_message
        self.check_message('Error', notification_message)


class UploadTemplateTestCase(ExcelMixin, TestCase):
    """Test uploading data for Template excel path"""

    @patch("excel.helpers.ExcelTemplateReader.check_species",
           return_value=[False, 'Rainbow trout'])
    def test_upload_crbanim_errors_with_species(self, my_check):
        """Testing importing with data into UID with errors in species"""

        message = "Some species are not loaded in UID database"
        notification_message = (
            'Error in importing data: Some species '
            'are not loaded in UID database: Rainbow '
            'trout')

        # check crbanim import fails
        self.check_errors(my_check, message, notification_message)

    @patch("excel.helpers.ExcelTemplateReader.check_sex",
           return_value=[False, 'unknown'])
    def test_upload_crbanim_errors_with_sex(self, my_check):
        """Testing importing with data into UID with errors"""

        message = "Not all Sex terms are loaded into database"
        notification_message = (
            'Error in importing data: Not all Sex '
            'terms are loaded into database: check '
            'for unknown in your dataset')

        # check crbanim import fails
        self.check_errors(my_check, message, notification_message)

    @patch("excel.helpers.ExcelTemplateReader.check_accuracies",
           return_value=(False, set(["Fake"])))
    def test_upload_crbanim_errors_with_accuracies(self, my_check):
        """Testing importing with data into UID with errors"""

        message = "Not all accuracy levels are defined in database"
        notification_message = (
            "Error in importing data: Not all accuracy "
            "levels are defined in database: check "
            "for {'Fake'} in your dataset")

        # check crbanim import fails
        self.check_errors(my_check, message, notification_message)


class ReloadTemplateTestCase(ExcelMixin, TestCase):
    """Simulate a template reload case. Load data as in
    UploadTemplateTestCase, then call test which reload the same data"""

    # override used fixtures
    fixtures = [
        'crbanim/auth',
        'excel/dictspecie',
        'excel/image_app',
        'excel/submission',
        'excel/speciesynonym'
    ]
