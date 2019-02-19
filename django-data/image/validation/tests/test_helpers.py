#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 22 14:28:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from image_validation import validation
from image_validation.static_parameters import ruleset_filename as \
    IMAGE_RULESET
from image_validation.ValidationResult import ValidationResultRecord

from django.test import TestCase

from image_app.models import Animal, Sample, Submission, Person, Name
from common.tests import PersonMixinTestCase


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
        self.rules = validation.read_in_ruleset(IMAGE_RULESET)
        self.submission_id = 1

    def test_animal(self):
        # at the time of writing this reference data raise one warning
        reference = [
            ("Warning", "Ontology provided for field EFABIS Breed country")]

        # get all animals
        animals = Animal.objects.all()

        # get all biosmaple data
        data = []

        for animal in animals:
            data += [animal.to_biosample()]

        for i, record in enumerate(data):
            result = self.rules.validate(record)

            # assert result type
            self.assertIsInstance(result, ValidationResultRecord)
            self.assertEqual(result.get_overall_status(), reference[i][0])

            def search(y):
                return reference[i][1] in y

            matches = [search(message) for message in result.get_messages()]
            self.assertIn(True, matches)

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

        for i, record in enumerate(data):
            result = self.rules.validate(record)

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
        usi_result = validation.check_usi_structure(data)

        # no errors for check usi_structure
        self.assertIsInstance(usi_result, list)
        self.assertEqual(len(usi_result), 0)

        # test for duplicated data
        dup_result = validation.check_duplicates(data)

        # no errors for check_duplicates
        self.assertIsInstance(dup_result, list)
        self.assertEqual(len(dup_result), 0)

    def test_wrong_json_structure(self):
        """Test that json structure is ok"""

        reference = [
            ('Wrong JSON structure: no title field for record with '
             'alias as animal_1'),
        ]

        # get my animal
        animal = Animal.objects.get(pk=1)
        data = animal.to_biosample()

        # delete some attributes from animal data
        del(data['title'])

        # test for Json structure
        test = validation.check_usi_structure([data])

        self.assertEqual(reference, test)


class RulesTestCase(TestCase):
    """Assert that image rules are valid"""

    def setUp(self):
        self.rules = validation.read_in_ruleset(IMAGE_RULESET)

    def test_check_ruleset(self):
        """Assert that rules are valid"""

        # get validation results
        ruleset_check = validation.check_ruleset(self.rules)

        # test image metadata rules
        self.assertIsInstance(ruleset_check, list)
        self.assertEqual(len(ruleset_check), 0)
