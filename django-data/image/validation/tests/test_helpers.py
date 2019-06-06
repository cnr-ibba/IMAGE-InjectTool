#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 22 14:28:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from image_validation.ValidationResult import ValidationResultRecord
from unittest.mock import patch

from django.test import TestCase

from image_app.models import Animal, Sample, Submission, Person, Name
from common.tests import PersonMixinTestCase

from ..helpers import (
    MetaDataValidation, ValidationSummary, OntologyCacheError)

from ..models import ValidationResult


class MetaDataValidationTestCase(TestCase):
    @patch("validation.helpers.validation.read_in_ruleset",
           side_effect=OntologyCacheError("test exception"))
    def test_issues_with_ebi(self, my_issue):
        """
        Test temporary issues related with OLS EBI server during
        image_validation.use_ontology.OntologyCache loading"""

        # assert issues from validation.helpers.validation.read_in_ruleset
        self.assertRaisesMessage(
            OntologyCacheError,
            "test exception",
            MetaDataValidation)

        # test mocked function called
        self.assertTrue(my_issue.called)


class SubmissionTestCase(PersonMixinTestCase, TestCase):
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
        self.metadata = MetaDataValidation()
        self.submission_id = 1

    def test_animal(self):
        # at the time of writing this reference data raise one warning
        reference = [
            ("Pass", "")]

        # get all animals
        animals = Animal.objects.all()

        # get all biosmaple data
        data = []

        for animal in animals:
            data += [animal.to_biosample()]

        # check for usi structure
        usi_result = self.metadata.check_usi_structure(data)
        self.assertEqual(usi_result, [])

        for i, record in enumerate(data):
            # validate record
            result = self.metadata.validate(record)

            # assert result type
            self.assertIsInstance(result, ValidationResultRecord)
            self.assertEqual(result.get_overall_status(), reference[i][0])

            def search(y):
                return reference[i][1] in y

            matches = [search(message) for message in result.get_messages()]
            self.assertNotIn(False, matches)

    def test_sample(self):
        # at the time of writing this reference pass without problems
        reference = [
            ("Pass", "")]

        # get all samples
        samples = Sample.objects.all()

        # get all biosmaple data
        data = []

        for sample in samples:
            data += [sample.to_biosample()]

        # check for usi structure
        usi_result = self.metadata.check_usi_structure(data)
        self.assertEqual(usi_result, [])

        for i, record in enumerate(data):
            result = self.metadata.validate(record)

            # assert result type
            self.assertIsInstance(result, ValidationResultRecord)
            self.assertEqual(result.get_overall_status(), reference[i][0])

            def search(y):
                return "" == y

            matches = [search(message) for message in result.get_messages()]
            self.assertNotIn(False, matches)

    def test_sample_update(self):
        """Simulate a validation for an already submitted sample"""

        # at the time of writing this reference pass without problems
        reference = [
            ("Pass", "")]

        # get all samples
        samples = Sample.objects.all()

        # get all biosmaple data
        data = []

        for i, sample in enumerate(samples):
            # modify animal and sample
            animal_reference = "SAMEA" + str(4450079 + i)
            sample.animal.name.biosample_id = animal_reference
            sample.animal.name.save()

            sample_reference = "SAMEA" + str(4450075 + i)
            sample.name.biosample_id = sample_reference
            sample.name.save()

            data += [sample.to_biosample()]

        # check for usi structure
        usi_result = self.metadata.check_usi_structure(data)
        self.assertEqual(usi_result, [])

        for i, record in enumerate(data):
            result = self.metadata.validate(record)

            # assert result type
            self.assertIsInstance(result, ValidationResultRecord)
            self.assertEqual(result.get_overall_status(), reference[i][0])

            def search(y):
                return "" == y

            matches = [search(message) for message in result.get_messages()]
            self.assertNotIn(False, matches)

    def test_submission(self):
        # get a submission
        submission = Submission.objects.get(pk=self.submission_id)

        # get all biosample data for animals
        animals_json = []
        samples_json = []

        # a more limited subset
        for animal in Animal.objects.filter(name__submission=submission):
            animals_json += [animal.to_biosample()]

            # get samples data and add to a list
            for sample in animal.sample_set.all():
                samples_json += [sample.to_biosample()]

        # collect all data in a dictionary
        data = animals_json + samples_json

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

        # get my animal
        animal = Animal.objects.get(pk=1)
        data = animal.to_biosample()

        # delete some attributes from animal data
        del(data['title'])

        # test for Json structure
        test = self.metadata.check_usi_structure([data])

        self.assertEqual(reference, test)


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
