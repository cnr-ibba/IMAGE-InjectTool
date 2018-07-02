#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 13:13:16 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

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

        response = self.client.post(url, data)

        # get context
        context = response.context

        # ket keys from context
        self.activation_key = context.get("activation_key")

        self.activation_url = reverse(
            "accounts:registration_activate",
            kwargs={'activation_key': self.activation_key})

        self.response = self.client.get(self.activation_url, follow=True)
        self.home_url = reverse('index')

    def test_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_user_authentication(self):
        '''
        Create a new request to an arbitrary page.
        The resulting response should now have a `user` to its context,
        '''

        # login user
        self.client.login(username='john', password='abcdef123456')
        response = self.client.get(self.home_url)
        user = response.context.get('user')
        self.assertTrue(user.is_authenticated)
