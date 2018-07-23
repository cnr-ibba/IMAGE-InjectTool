#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 29 13:54:49 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse, resolve

from image_app.models import User

from ..forms import MyAccountForm
from ..views import MyAccountView


class Basetest(TestCase):
    def setUp(self):
        # create a testuser
        User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        self.client = Client()
        self.client.login(username='test', password='test')

        # get the url for dashboard
        self.url = reverse('accounts:my_account')
        self.response = self.client.get(self.url)

    def check_messages(self, response, tag, message_text):
        """Check that a response has warnings"""

        # each element is an instance
        # of django.contrib.messages.storage.base.Message
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        for message in all_messages:
            self.assertTrue(tag in message.tags)
            self.assertEqual(
                message.message,
                message_text)


class MyAccountViewTest(Basetest):
    def test_redirection(self):
        '''Non Authenticated user are directed to login page'''

        login_url = reverse("login")
        client = Client()
        response = client.get(self.url)

        self.assertRedirects(
            response, '{login_url}?next={url}'.format(
                login_url=login_url, url=self.url)
        )

    def test_myaccount_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_myaccount_url_resolves_myaccount_view(self):
        view = resolve('/accounts/my_account/')
        self.assertIsInstance(view.func.view_class(), MyAccountView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')

        self.assertIsInstance(form, MyAccountForm)

    def test_form_inputs(self):
        '''
        The view must contain eleven inputs: csrf, username, first_name,
        last_name, email, password1, password2, affiliation, role,
        organization and agree_gdpr checkbox
        '''

        # total input is type=text + type=email + type=hidden (CSRF)
        self.assertContains(self.response, '<input', 5)
        self.assertContains(self.response, 'type="text"', 3)
        self.assertContains(self.response, 'type="email"', 1)


class SuccessfulMyAccountViewTests(Basetest):
    fixtures = [
        "dictcountry.json", "dictrole.json", "organization.json"
    ]

    def setUp(self):
        # create a test user
        super().setUp()

        # MyAccountForm is a multiform object, so input type name has the
        # name of the base form and the name of the input type
        self.data = {
            'user-first_name': 'John',
            'user-last_name': 'Doe',
            'user-email': 'john@doe.com',
            'person-affiliation': 1,
            'person-role': 1,
        }

        self.response = self.client.post(self.url, self.data)
        self.dashboard_url = reverse('image_app:dashboard')

    def test_redirection(self):
        '''
        A valid form submission should redirect the user to the home page
        '''
        self.assertRedirects(self.response, self.dashboard_url)

    def test_user_updated(self):
        user = User.objects.get(username='test')

        for attribute in ['first_name', 'last_name', 'email']:
            test = getattr(user, attribute)
            key = "user-%s" % (attribute)
            reference = self.data[key]
            self.assertEqual(reference, test, "Checking %s" % (attribute))

        # get person object
        person = user.person

        # checking person references
        for attribute in ['role', 'affiliation']:
            test = getattr(person, "%s_id" % (attribute))
            key = "person-%s" % (attribute)
            reference = self.data[key]
            self.assertEqual(reference, test, "Checking %s" % (attribute))


class InvalidMyAccountViewTests(Basetest):
    def setUp(self):
        # create a test user
        super().setUp()

        # submit an empty dictionary
        self.response = self.client.post(self.url, {})

    def test_signup_status_code(self):
        '''
        An invalid form submission should return to the same page
        '''
        self.assertEquals(self.response.status_code, 200)

    def test_form_errors(self):
        multi_form = self.response.context.get('form')
        for form in multi_form.forms.values():
            self.assertGreater(len(form.errors), 0)

    def test_form_messages(self):
        self.check_messages(
            self.response,
            "error",
            "Please correct the errors below")
