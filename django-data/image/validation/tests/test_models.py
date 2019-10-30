#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 16:56:43 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from ..models import ValidationSummary


class ValidationSummaryTestCase(TestCase):
    """Testing ValidationSummary class"""

    fixtures = [
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user',
        'validation/validationsummary',
    ]

    def setUp(self):
        self.vs_animal = ValidationSummary.objects.get(pk=1)
        self.vs_sample = ValidationSummary.objects.get(pk=2)

    def test_reset_all_count(self):
        # set a different count objects
        self.vs_animal.all_count = 99
        self.vs_animal.save()

        self.vs_sample.all_count = 99
        self.vs_sample.save()

        # now call methods
        self.vs_animal.reset_all_count()
        self.vs_sample.reset_all_count()

        # assert true values (calculated accordingly Animals and Samples)
        self.assertEqual(self.vs_animal.all_count, 3)
        self.assertEqual(self.vs_sample.all_count, 1)

    def test_reset_all_count_unsupported(self):
        """Created a non supported validation summary and check
        that exceptions are raised"""

        # TODO: type should be an enum value so this test should be removed
        vs_test = ValidationSummary(type="test", all_count=99)
        self.assertRaisesMessage(
            Exception,
            "Unknown type 'test'",
            vs_test.reset_all_count)
