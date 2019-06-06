#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 22 14:28:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import json

from image_validation.ValidationResult import ValidationResultRecord
from unittest.mock import patch, Mock

from django.test import TestCase

from image_app.models import Animal, Sample, Submission, Person, Name
from common.tests import PersonMixinTestCase

from ..helpers import (
    MetaDataValidation, ValidationSummary, OntologyCacheError)

from ..models import ValidationResult


class MetaDataValidationTestCase(TestCase):
    @patch("validation.helpers.validation.read_in_ruleset",
           side_effect=json.JSONDecodeError("meow", "woof", 42))
    def test_issues_with_ebi(self, my_issue):
        """
        Test temporary issues related with OLS EBI server during
        image_validation.use_ontology.OntologyCache loading"""

        # assert issues from validation.helpers.validation.read_in_ruleset
        self.assertRaisesMessage(
            OntologyCacheError,
            "Issue with 'https://www.ebi.ac.uk/ols/api/'",
            MetaDataValidation)

        # test mocked function called
        self.assertTrue(my_issue.called)

    @patch("requests.get")
    @patch("validation.helpers.validation.read_in_ruleset")
    def test_check_biosample_id_target(self, my_read, mock_get):
        """Test fecthing biosample ids from MetaDataValidation"""

        # paching response
        response = Mock()
        response.status_code = 200
        mock_get.return_value = response

        # create a fake ValidationResultRecord
        record_result = ValidationResultRecord(record_id="test")

        # get a metadata object
        metadata = MetaDataValidation()

        # check biosample object
        record_result = metadata.check_biosample_id_target(
            "FAKEA123456", "test", record_result)

        # test pass status and no messages
        self.assertEqual(record_result.get_overall_status(), 'Pass')
        self.assertEqual(record_result.get_messages(), [])

        # assert my methods called
        self.assertTrue(my_read.called)
        self.assertTrue(mock_get.called)

    @patch("requests.get")
    @patch("validation.helpers.validation.read_in_ruleset")
    def test_check_biosample_id_issue(self, my_read, mock_get):
        """No valid biosample is found for this object"""

        # paching response
        response = Mock()
        response.status_code = 404
        mock_get.return_value = response

        # create a fake ValidationResultRecord
        record_result = ValidationResultRecord(record_id="test")

        # get a metadata object
        metadata = MetaDataValidation()

        # check biosample object
        record_result = metadata.check_biosample_id_target(
            "FAKEA123456", "test", record_result)

        # test Warning status and one message
        self.assertEqual(record_result.get_overall_status(), 'Warning')
        self.assertEqual(len(record_result.get_messages()), 1)

        # assert my methods called
        self.assertTrue(my_read.called)
        self.assertTrue(mock_get.called)


class SubmissionMixin(PersonMixinTestCase):
    # an attribute for PersonMixinTestCase
    person = Person

    fixtures = [
        'image_app/animal',
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
        'image_app/name',
        'image_app/ontology',
        'image_app/organization',
        'image_app/publication',
        'image_app/sample',
        'image_app/submission',
        'image_app/user'
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        # drop publication for semplicity
        name = Name.objects.get(pk=3)
        publication = name.publication
        publication.delete()

    def setUp(self):
        # calling my base class setup
        super().setUp()

        self.metadata = MetaDataValidation()


class SubmissionTestCase(SubmissionMixin, TestCase):
    """Deal real tests using image_validation library: this want to ensure
    that InjectTools can work with image_validation"""

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # get an animal object
        self.animal = Animal.objects.get(pk=1)
        self.animal_record = self.animal.to_biosample()

        # get a sample object
        self.sample = Sample.objects.get(pk=1)
        self.sample_record = self.sample.to_biosample()

    def test_animal(self):
        """Testing an animal submission"""

        # at the time of writing this reference data raise one warning
        reference = ("Pass", "")

        # check for usi structure
        usi_result = self.metadata.check_usi_structure([self.animal_record])
        self.assertEqual(usi_result, [])

        # validate record
        result = self.metadata.validate(self.animal_record)

        # assert result type
        self.assertIsInstance(result, ValidationResultRecord)
        self.assertEqual(result.get_overall_status(), reference[0])

        def search(y):
            return reference[1] in y

        matches = [search(message) for message in result.get_messages()]
        self.assertNotIn(False, matches)

    def test_sample(self):
        """Test a sample submission"""

        # at the time of writing this reference pass without problems
        reference = ("Pass", "")

        # check for usi structure
        usi_result = self.metadata.check_usi_structure([self.sample_record])
        self.assertEqual(usi_result, [])

        result = self.metadata.validate(self.sample_record)

        # assert result type
        self.assertIsInstance(result, ValidationResultRecord)
        self.assertEqual(result.get_overall_status(), reference[0])

        def search(y):
            return reference[1] == y

        matches = [search(message) for message in result.get_messages()]
        self.assertNotIn(False, matches)

    def test_sample_relationship_issue(self):
        """Testing an error with related alias. Not sure if it can happen or
        not"""

        # get record from sample
        record = self.sample_record

        # change alias in relationship in order to have no a related obj
        record["sampleRelationships"] = [{
            "alias": "IMAGEA999999999",
            "relationshipNature": "derived from"
        }]

        # create a fake ValidationResultRecord
        record_result = ValidationResultRecord(record_id=record['title'])

        # check relationship method
        related, result = self.metadata.check_relationship(
            record, record_result)

        # this is an error in results
        self.assertEqual(related, [])
        self.assertEqual(result.get_overall_status(), 'Error')
        self.assertIn(
            "Could not locate the referenced record",
            result.get_messages()[0])

    def test_submission(self):
        """Testing usi_structure and duplicates in a submission"""

        # get all biosample data in a list
        data = [self.animal_record, self.sample_record]

        # test for usi structure
        usi_result = self.metadata.check_usi_structure(data)

        # no errors for check usi_structure
        self.assertIsInstance(usi_result, list)
        self.assertEqual(len(usi_result), 0)

        # test for duplicated data
        dup_result = self.metadata.check_duplicates(data)

        # no errors for check_duplicates
        self.assertIsInstance(dup_result, list)
        self.assertEqual(len(dup_result), 0)

    def test_wrong_json_structure(self):
        """Test that json structure is ok"""

        reference = [
            ('Wrong JSON structure: no title field for record with '
             'alias as IMAGEA000000001'),
        ]

        # delete some attributes from animal data
        del(self.animal_record['title'])

        # test for Json structure
        test = self.metadata.check_usi_structure([self.animal_record])

        self.assertEqual(reference, test)


class SampleUpdateTestCase(SubmissionMixin, TestCase):
    """Testing validation for a sample update"""

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # get a samlple
        self.sample = Sample.objects.get(pk=1)

        # modify animal and sample
        self.animal_reference = "SAMEA4450079"
        self.sample.animal.name.biosample_id = self.animal_reference
        self.sample.animal.name.save()

        self.sample_reference = "SAMEA4450075"
        self.sample.name.biosample_id = self.sample_reference
        self.sample.name.save()

        self.record = self.sample.to_biosample()

    def test_sample_update(self):
        """Simulate a validation for an already submitted sample"""

        # at the time of writing this reference pass without problems
        reference = ("Pass", "")

        # check object
        result = self.metadata.validate(self.record)

        # assert result type
        self.assertIsInstance(result, ValidationResultRecord)
        self.assertEqual(result.get_overall_status(), reference[0])

        def search(y):
            return reference[1] == y

        matches = [search(message) for message in result.get_messages()]
        self.assertNotIn(False, matches)


class RulesTestCase(TestCase):
    """Assert that image rules are valid"""

    def setUp(self):
        self.metadata = MetaDataValidation()

    def test_check_ruleset(self):
        """Assert that rules are valid"""

        # get validation results
        ruleset_check = self.metadata.check_ruleset()

        # test image metadata rules
        self.assertIsInstance(ruleset_check, list)
        self.assertEqual(len(ruleset_check), 0)


class ValidationSummaryTestCase(TestCase):
    fixtures = [
        'image_app/animal',
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
        'image_app/name',
        'image_app/organization',
        'image_app/publication',
        'image_app/submission',
        'image_app/user',
        'image_app/sample',
        'validation/validationresult'
    ]

    def setUp(self):
        self.submission = Submission.objects.get(pk=1)
        self.validationsummary = ValidationSummary(self.submission)

        # set names
        self.animal_name = Name.objects.get(pk=3)
        self.sample_name = Name.objects.get(pk=4)

        # track validationresult object
        self.validationresult = ValidationResult.objects.get(pk=1)

    def test_initialization(self):
        """Test that ValidationSummary is correctly initialized"""

        self.assertEqual(self.validationsummary.n_animal_issues, 0)
        self.assertEqual(self.validationsummary.n_sample_issues, 0)

        self.assertEqual(self.validationsummary.n_animal_unknown, 0)
        self.assertEqual(self.validationsummary.n_sample_unknown, 1)

    def test_process_errors(self):
        report = self.validationsummary.process_errors()
        self.assertIsInstance(report, dict)
        self.assertEqual(report, {})

    def update_message(self, message):
        self.validationresult.status = "Error"
        self.validationresult.messages = [message]
        self.validationresult.save()

    def test_process_error_unmanaged(self):
        # modify validation results object
        message = "Unmanaged error"
        self.update_message(message)

        with self.assertLogs('validation.helpers', level="ERROR") as log:
            report = self.validationsummary.process_errors()

        self.assertEqual(len(report), 1)

        # log.output is a list of rows for each logger message
        self.assertEqual(len(log.output), 1)
        self.assertIn("Cannot parse: '%s'" % message, log.output[0])

    def test_patterns1(self):
        # define test strings for patterns
        message = (
            'Error: <link> of field Availability is message for Record test')
        self.update_message(message)

        with self.assertLogs('validation.helpers', level="DEBUG") as log:
            report = self.validationsummary.process_errors()

        self.assertEqual(len(report), 1)
        self.assertEqual(len(log.output), 2)
        self.assertIn(
            "DEBUG:validation.helpers:parse1: Got 'link','Availability' and "
            "'message'",
            log.output)

    def test_patterns2(self):
        # define test strings for patterns
        message = (
            'reason meow for the field myfield which blah, blah for Record '
            'test')
        self.update_message(message)

        with self.assertLogs('validation.helpers', level="DEBUG") as log:
            report = self.validationsummary.process_errors()

        self.assertEqual(len(report), 1)
        self.assertEqual(len(log.output), 2)
        self.assertIn(
            "DEBUG:validation.helpers:parse2: Got 'reason meow','myfield' "
            "and 'blah, blah'",
            log.output)

    def test_patterns3(self):
        # define test strings for patterns
        message = (
            'Provided value term does not match to the provided ontology '
            'for Record test')
        self.update_message(message)

        with self.assertLogs('validation.helpers', level="DEBUG") as log:
            report = self.validationsummary.process_errors()

        self.assertEqual(len(report), 1)
        self.assertEqual(len(log.output), 2)
        self.assertIn(
            "DEBUG:validation.helpers:parse3: Got 'term' and 'does not match "
            "to the provided ontology'",
            log.output)

    def test_update_message(self):
        # define an error message as for test_pattern1
        message = (
            'Error: <link> of field Availability is message for Record test')
        self.update_message(message)

        # get another validation result object and assign errors
        validationresult = ValidationResult()
        validationresult.status = "Error"
        validationresult.messages = [message]
        validationresult.name = self.sample_name
        validationresult.save()

        with self.assertLogs('validation.helpers', level="DEBUG") as log:
            report = self.validationsummary.process_errors()

        self.assertEqual(len(report), 1)
        self.assertEqual(len(log.output), 4)
        self.assertIn(
            "DEBUG:validation.helpers:parse1: Got 'link','Availability' and "
            "'message'",
            log.output)
