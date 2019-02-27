#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 13:55:39 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from image_app.models import Sample

from ..forms import UpdateSampleForm
from .common import SampleFeaturesMixin


class UpdateSampleFormTest(SampleFeaturesMixin, TestCase):
    def setUp(self):
        self.sample = Sample.objects.get(pk=1)
        self.form = UpdateSampleForm(self.sample)

    def test_form_has_fields(self):
        """Testing against fields"""

        expected = [
            'disabled_name',
            'alternative_id',
            'description',
            'disabled_animal',
            'protocol',
            'collection_date',
            'collection_place_latitude',
            'collection_place_longitude',
            'collection_place',
            'collection_place_accuracy',
            'organism_part',
            'developmental_stage',
            'physiological_stage',
            'animal_age_at_collection',
            'animal_age_at_collection_units',
            'availability',
            'storage',
            'storage_processing',
            'preparation_interval'
        ]
        actual = list(self.form.fields)
        self.assertSequenceEqual(expected, actual)

    def test_form_disabled_fields(self):
        """Testing the disabled fields"""

        disabled_fields = [
            "disabled_name",
            "disabled_animal"
        ]

        for field_name in disabled_fields:
            test_field = self.form.fields[field_name]
            self.assertTrue(test_field.disabled)
