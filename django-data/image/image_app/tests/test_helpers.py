#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 10:34:44 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import TestCase

from image_app.models import Animal, Sample

from ..helpers import get_model_object


class GetModelObjectTestCase(TestCase):
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
        'image_app/sample',
        'image_app/submission',
        'image_app/user',
    ]

    def setUp(self):
        self.animal_id = 1
        self.sample_id = 1

    def test_get_model_object(self):

        test = get_model_object("Animal", 1)
        self.assertEqual(test.id, self.animal_id)
        self.assertIsInstance(test, Animal)

        test = get_model_object("Sample", 1)
        self.assertEqual(test.id, self.sample_id)
        self.assertIsInstance(test, Sample)

        # assert errors
        self.assertRaisesMessage(
            Exception,
            "Unknown table",
            get_model_object,
            "Name",
            1)
