#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 10:28:22 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from ..forms import SpecieSynonymForm


class SpecieSynonymFormTest(TestCase):
    def test_form_has_fields(self):
        form = SpecieSynonymForm()
        expected = ['word', 'language', 'dictspecie']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)
