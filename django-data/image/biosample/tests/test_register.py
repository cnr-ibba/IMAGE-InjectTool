#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 16:01:20 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os

from decouple import AutoConfig

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse, resolve
from django.conf import settings

from ..forms import RegisterUserForm
from ..views import RegisterUserView


# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


class Basetest(TestCase):
    fixtures = [
        "managed.json"
    ]

    def setUp(self):
        User = get_user_model()

        # create a testuser
        User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        self.client = Client()
        self.client.login(username='test', password='test')

        # get the url for dashboard
        self.url = reverse('biosample:register')
        self.response = self.client.get(self.url)

    def check_messages(self, response, tag, message_text):
        """Check that a response has warnings"""

        # each element is an instance
        # of django.contrib.messages.storage.base.Message
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        found = False

        # I can have moltiple message, and maybe I need to find a specific one
        for message in all_messages:
            if tag in message.tags and message_text in message.message:
                print(tag)
                print(message.tags)
                print(message_text)
                print(message.message)
                found = True

        self.assertTrue(found)


class RegisterUserViewTest(Basetest):
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
        view = resolve('/biosample/register/')
        self.assertIsInstance(view.func.view_class(), RegisterUserView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')

        self.assertIsInstance(form, RegisterUserForm)

    def test_form_inputs(self):
        '''
        The view must contain eleven inputs: csrf, username, first_name,
        last_name, email, password1, password2, affiliation, role,
        organization and agree_gdpr checkbox
        '''

        # total input is n of form fields + (CSRF)
        self.assertContains(self.response, '<input', 4)
        self.assertContains(self.response, 'type="text"', 2)
        self.assertContains(self.response, 'type="password"', 1)


class SuccessfulRegisterUserViewTests(Basetest):
    def setUp(self):
        """Test registration with valid data"""

        # create a test user
        super().setUp()

        self.data = {
            'name': config('USI_USER'),
            'password': config('USI_PASSWORD'),
            'team': 'subs.test-team-6',
        }

        self.response = self.client.post(self.url, self.data)
        self.dashboard_url = reverse('image_app:dashboard')

    def test_redirection(self):
        '''
        A valid form submission should redirect the user to the home page
        '''

        self.assertRedirects(self.response, self.dashboard_url)
        self.check_messages(self.response, "success", "Account registered")

    def test_registered_redirect(self):
        """Test that an already registered user will get a redirect url"""

        # get the registering page and check that is a redirect
        response = self.client.get(self.url)
        self.assertRedirects(response, self.dashboard_url)
        self.check_messages(
            response,
            "warning",
            "Your biosample account is already registered"
        )


class InvalidRegisterUserViewTests(Basetest):
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
        form = self.response.context.get('form')
        self.assertGreater(len(form.errors), 0)

    def test_form_messages(self):
        self.check_messages(
            self.response,
            "error",
            "Please correct the errors below")


class InvalidUsiDataTests(Basetest):
    """Test the register class with invalid usi data"""

    def test_invalid_name(self):
        self.data = {
            'name': 'test',
            'password': config('USI_PASSWORD'),
            'team': 'subs.test-team-6',
        }

        response = self.client.post(self.url, self.data)
        self.assertEquals(response.status_code, 200)
        self.check_messages(response, "error", "Unable to generate token")

    def test_invalid_pass(self):
        self.data = {
            'name': config('USI_USER'),
            'password': 'test',
            'team': 'subs.test-team-6',
        }

        response = self.client.post(self.url, self.data)
        self.assertEquals(response.status_code, 200)
        self.check_messages(response, "error", "Unable to generate token")

    def test_invalid_team(self):
        """User doesn't belong to a team"""

        self.data = {
            'name': config('USI_USER'),
            'password': config('USI_PASSWORD'),
            'team': 'subs.test-team-7',
        }

        response = self.client.post(self.url, self.data)
        self.assertEquals(response.status_code, 200)
        self.check_messages(
            response, "error", "You don't belong to team:")

    def test_invalid_team2(self):
        """biosample manager doesn't belong to team"""

        self.data = {
            'name': config('USI_USER'),
            'password': config('USI_PASSWORD'),
            'team': 'subs.test-team-3',
        }

        response = self.client.post(self.url, self.data)
        self.assertEquals(response.status_code, 200)
        self.check_messages(
            response,
            "error",
            "team subs.test-team-3 is not managed by InjectTool")
