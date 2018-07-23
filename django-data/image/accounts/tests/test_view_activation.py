#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 13:13:16 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Testing activation keys and views

"""

from django.test import TestCase, Client
from django.urls import reverse, resolve

from ..views import ActivationView, ActivationComplete
from ..models import create_key


class BaseTest(TestCase):
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
            'person-affiliation': 1,
            'person-role': 1,
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

        # I don't need to login to see this page, since I need to activate
        # my account to login
        self.response = self.client.get(self.activation_url, follow=True)
        self.complete = reverse('accounts:registration_activation_complete')


class ActivationTest(BaseTest):
    def test_redirect(self):
        self.assertRedirects(self.response, self.complete)

    def test_user_authentication(self):
        '''
        After following activation link, I'm logged on the site
        '''

        # login user
        user = self.response.context.get('user')
        self.assertTrue(user.is_authenticated)

    def test_url_resolves_view(self):
        view = resolve('/accounts/activate/%s/' % (self.activation_key))
        self.assertIsInstance(view.func.view_class(), ActivationView)

    def test_reusing_keys(self):
        """a user use its old key for activation"""

        response = self.client.get(self.activation_url, follow=True)
        self.assertRedirects(response, self.complete)

    def test_using_a_different_key(self):
        """Use another key for activation"""

        activation_url = reverse(
            "accounts:registration_activate",
            kwargs={'activation_key': create_key()})

        response = self.client.get(activation_url, follow=True)
        self.assertContains(response, "Account activation failed")


class ActivationCompleteTest(BaseTest):
    def setUp(self):
        super(ActivationCompleteTest, self).setUp()

        # get the url for registration_activation_complete
        self.url = reverse('accounts:registration_activation_complete')

        # get a response
        self.response = self.client.get(self.url)

    def test_redirection(self):
        '''Non Authenticated user are directed to login page'''

        login_url = reverse("login")
        client = Client()
        response = client.get(self.url)

        self.assertRedirects(
            response, '{login_url}?next={url}'.format(
                login_url=login_url, url=self.url)
        )

    def test_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_url_resolves_view(self):
        view = resolve('/accounts/activate/complete/')
        self.assertIsInstance(view.func.view_class(), ActivationComplete)

    def test_contains_navigation_links(self):
        register_url = reverse('biosample:register')
        create_url = reverse('biosample:create')

        self.assertContains(self.response, 'href="{0}"'.format(register_url))
        self.assertContains(self.response, 'href="{0}"'.format(create_url))
