#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 13:55:39 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from image_app.models import Animal

from ..forms import UpdateAnimalForm
from .common import AnimalFeaturesMixin


class UpdateAnimalFormTest(AnimalFeaturesMixin, TestCase):
    def setUp(self):
        self.animal = Animal.objects.get(pk=1)
        self.form = UpdateAnimalForm(self.animal)

    def test_form_has_fields(self):
        """Testing against fields"""

        expected = [
            'disabled_name',
            'alternative_id',
            'description',
            'breed',
            'sex',
            'disabled_mother',
            'disabled_father',
            'birth_location',
            'birth_location_latitude',
            'birth_location_longitude',
            'birth_location_accuracy'
        ]
        actual = list(self.form.fields)
        self.assertSequenceEqual(expected, actual)

    def test_form_disabled_fields(self):
        """Testing the disabled fields"""

        disabled_fields = [
            "disabled_name",
            "disabled_mother",
            "disabled_father"
        ]

        for field_name in disabled_fields:
            test_field = self.form.fields[field_name]
            self.assertTrue(test_field.disabled)
