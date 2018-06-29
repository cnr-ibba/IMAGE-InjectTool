#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 29 13:54:49 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from ..forms import UserForm, PersonForm, MyAccountForm


class UserFormTest(TestCase):
    def test_form_has_fields(self):
        form = UserForm()
        expected = ['first_name', 'last_name', 'email']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)


class PersonFormTest(TestCase):
    def test_form_has_fields(self):
        form = PersonForm()
        expected = ['initials', 'affiliation', 'role', 'organization']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)


class MyAccountFormTest(TestCase):
    def test_form_has_fields(self):
        form = MyAccountForm()
        expected = [
            'first_name', 'last_name', 'email', 'initials', 'affiliation',
            'role', 'organization']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)
