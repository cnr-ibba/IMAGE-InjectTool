#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 14:48:24 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from ..forms import OrganizationForm


class OrganizationFormTest(TestCase):
    def test_form_has_fields(self):
        form = OrganizationForm()
        expected = ['name', 'address', 'country', 'URI', 'role']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)
