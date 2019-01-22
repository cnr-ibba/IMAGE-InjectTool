#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 22 14:28:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import json

from django.test import TestCase

from image_app.models import Animal, Sample, Submission, Person
from common.tests import PersonMixinTestCase

from ..helpers import validation
from ..helpers.ValidationResult import ValidationResultRecord
from ..constants import IMAGE_RULESET


class SubmissionTestCase(PersonMixinTestCase, TestCase):
    # an attribute for PersonMixinTestCase
    person = Person

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission",
        "biosample/account",
        "biosample/managedteam",
        "image_app/dictsex",
        "image_app/dictspecie",
        "image_app/dictbreed",
        "image_app/name",
        "image_app/animal",
        "image_app/sample",
        "image_app/ontology"
    ]

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

        # get validation results
        ruleset_results = validation.check_with_ruleset(data, self.rules)

        # test objects
        self.assertIsInstance(ruleset_results, list)

        for i, result in enumerate(ruleset_results):
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

        # get validation results
        ruleset_results = validation.check_with_ruleset(data, self.rules)

        # test objects
        self.assertIsInstance(ruleset_results, list)

        for i, result in enumerate(ruleset_results):
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
