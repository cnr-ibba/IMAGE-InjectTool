#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 13:13:16 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.core import mail
from django.test import TestCase
from django.urls import reverse


class ActivationTest(TestCase):
    fixtures = [
        "dictcountry.json", "dictrole.json", "organization.json"
    ]

    def setUp(self):
        url = reverse('accounts:registration_register')

        # SignUpForm is a multiform object, so input type name has the name of
        # the base form and the name of the input type
        data = {
            'user-username': 'john',
            'user-first_name': 'John',
            'user-last_name': 'Doe',
            'user-email': 'john@doe.com',
            'user-password1': 'abcdef123456',
            'user-password2': 'abcdef123456',
            'person-affiliation': 'IBBA',
            'person-role': 1,
            'person-organization': 1,
            'person-agree_gdpr': True
        }
        self.response = self.client.post(url, data)

        # read mail
        self.email = mail.outbox[0]

    def test_email_subject(self):
        self.assertEqual(
            '[IMAGE-InjectTool] Confirm registration',
            self.email.subject)

    def test_email_body(self):
        # get context
        context = self.response.context

        # ket keys from context
        activation_key = context.get("activation_key")
        site = context.get('site')

        activation_url = "http://{site}/accounts/activate/{key}/".format(
            site=site, key=activation_key)

        self.assertIn(activation_url, self.email.body)

    def test_email_to(self):
        self.assertEqual(['john@doe.com'], self.email.to)