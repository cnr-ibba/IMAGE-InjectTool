#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 16:01:20 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import resolve, reverse

from ..forms import RegisterUserForm
from ..models import ManagedTeam
from ..views import RegisterUserView
from .test_token import generate_token


class Basetest(TestCase):
    fixtures = [
        "biosample/managedteam.json"
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        # adding mock objects
        cls.mock_get_patcher = patch('pyUSIrest.auth.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_get_patcher.stop()

        # calling base method
        super().tearDownClass()

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
        self.assertEqual(self.response.status_code, 200)

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
        self.assertContains(self.response, '<input', 3)
        self.assertContains(self.response, '<select', 1)
        self.assertContains(self.response, 'type="text"', 1)
        self.assertContains(self.response, 'type="password"', 1)


class SuccessfulRegisterUserViewTests(Basetest):
    def setUp(self):
        """Test registration with valid data"""

        # create a test user
        super().setUp()

        # generate tocken
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = generate_token()
        self.mock_get.return_value.status_code = 200

        # get a team
        team1 = ManagedTeam.objects.get(name='subs.test-team-1')

        self.data = {
            'name': 'image-test',
            'password': 'image-password',
            'team': team1.id,
        }

        self.response = self.client.post(self.url, self.data)
        self.dashboard_url = reverse('uid:dashboard')

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
            "Your AAP profile is already registered"
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
        self.assertEqual(self.response.status_code, 200)

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

    def setUp(self):
        # create a test user
        super().setUp()

        # get a team
        self.team1 = ManagedTeam.objects.get(name='subs.test-team-1')
        self.team2 = ManagedTeam.objects.get(name='subs.test-team-2')

        # set invalid string
        self.invalid_str = (
            '{"timestamp":1531839735063,"status":401,"error":"Unauthorized",'
            '"message":"Bad credentials","path":"/auth"}')

    def test_invalid_name(self):
        # generate tocken
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = self.invalid_str
        self.mock_get.return_value.status_code = 401

        self.data = {
            'name': 'invalid-name',
            'password': 'image-password',
            'team': self.team1.id,
        }

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.check_messages(response, "error", "Unable to generate token")

    def test_invalid_pass(self):
        # generate tocken
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = self.invalid_str
        self.mock_get.return_value.status_code = 401

        self.data = {
            'name': 'image-test',
            'password': 'invalid-password',
            'team': self.team1.id,
        }

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.check_messages(response, "error", "Unable to generate token")

    def test_invalid_team(self):
        """User doesn't belong to a team"""

        # generate tocken
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = generate_token()
        self.mock_get.return_value.status_code = 200

        self.data = {
            'name': 'image-test',
            'password': 'image-password',
            'team': self.team2.id,
        }

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.check_messages(
            response, "error", "You don't belong to team:")
