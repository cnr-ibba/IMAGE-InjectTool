#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 16:04:18 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from ..forms import (
    GenerateTokenForm, CreateUserForm, RegisterUserForm, SubmitForm)


class GenerateTokenFormTest(TestCase):
    def test_form_has_fields(self):
        form = GenerateTokenForm()
        expected = ['user', 'password']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)


class RegisterUserFormTest(TestCase):
    def test_form_has_fields(self):
        form = RegisterUserForm()
        expected = sorted(['name', 'password', 'team'])
        actual = sorted(list(field.name for field in form))
        self.assertSequenceEqual(expected, actual)


class CreateUserFormTest(TestCase):
    def test_form_has_fields(self):
        form = CreateUserForm()
        expected = sorted(['password1', 'password2'])
        actual = sorted(list(field.name for field in form))
        self.assertSequenceEqual(expected, actual)


class SubmitFormTest(TestCase):
    def test_form_has_fields(self):
        form = SubmitForm()
        expected = ['submission_id']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)
