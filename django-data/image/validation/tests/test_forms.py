#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 12:04:18 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from ..forms import ValidateForm


class ValidateFormTest(TestCase):
    def test_form_has_fields(self):
        form = ValidateForm()
        expected = ['submission_id']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)
