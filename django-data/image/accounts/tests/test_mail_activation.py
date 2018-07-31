#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 13:13:16 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Test sending mail with activation keys

"""

import datetime

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from django.conf import settings


class ActivationTest(TestCase):
    fixtures = [
        "accounts/dictcountry.json",
        "accounts/dictrole.json",
        "accounts/organization.json"
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
            'person-affiliation': '1',
            'person-role': 1,
            'person-agree_gdpr': True
        }
        self.response = self.client.post(url, data)

        # read mail
        self.email = mail.outbox[0]

        # detemine activation url
        self.activation_url = self.get_activation_url(self.response.context)

    def get_activation_url(self, context):
        # get keys from context
        activation_key = context.get("activation_key")
        site = context.get('site')

        # get activation url
        return "http://{site}/accounts/activate/{key}/".format(
            site=site, key=activation_key)

    def test_email_subject(self):
        self.assertEqual(
            '[IMAGE-InjectTool] Confirm registration',
            self.email.subject)

    def test_email_body(self):
        """Test activation url in mail"""

        self.assertIn(self.activation_url, self.email.body)

    def test_email_to(self):
        self.assertEqual(['john@doe.com'], self.email.to)

    def test_email_resend(self):
        """When clicking on resend activation button, a new mail is sent"""

        url = reverse("accounts:registration_resend_activation")
        data = {'email': 'john@doe.com'}
        self.client.post(url, data)

        # get a new mail
        self.assertEqual(len(mail.outbox), 2)
        email = mail.outbox[-1]

        # assert activation key is the same
        self.assertIn(self.activation_url, email.body)

    def test_email_resend_newkey(self):
        """rensend a mail with a new key if it is expired"""

        # find user
        user = User.objects.get(username='john')

        # Set date_joined previous than now + ACTIVATION_DAYS
        user.date_joined -= datetime.timedelta(
            days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        user.save()

        url = reverse("accounts:registration_resend_activation")
        data = {'email': 'john@doe.com'}
        response = self.client.post(url, data)

        # get a new mail
        self.assertEqual(len(mail.outbox), 2)
        email = mail.outbox[-1]

        # assert activation key different
        self.assertNotIn(self.activation_url, email.body)

        # determine a new key
        activation_url = self.get_activation_url(response.context)

        # assert activation key is the same
        self.assertIn(activation_url, email.body)
