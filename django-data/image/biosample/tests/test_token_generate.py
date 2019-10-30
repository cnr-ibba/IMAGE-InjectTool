#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 17 14:52:13 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import resolve, reverse

from ..forms import GenerateTokenForm
from ..models import Account, ManagedTeam
from ..views import GenerateTokenView
from .session_enabled_test_case import SessionEnabledTestCase
from .common import generate_token


class BaseTest(SessionEnabledTestCase):
    fixtures = [
        "biosample/managedteam"
    ]

    def setUp(self):
        User = get_user_model()

        # create a testuser
        user = User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        team = ManagedTeam.objects.get(name="subs.test-team-1")
        Account.objects.create(
            user=user, team=team, name="image-test")

        self.client = Client()
        self.client.login(username='test', password='test')

        # get the url for dashboard
        self.url = reverse('biosample:token-generation')
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


class CreateAuthViewTest(BaseTest):
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
        view = resolve('/biosample/token/generate/')
        self.assertIsInstance(view.func.view_class(), GenerateTokenView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')

        self.assertIsInstance(form, GenerateTokenForm)

    def test_form_inputs(self):
        '''
        The view must contain eleven inputs: csrf, username, first_name,
        last_name, email, password1, password2, affiliation, role,
        organization and agree_gdpr checkbox
        '''

        # total input is n of form fields + (CSRF)
        self.assertContains(self.response, '<input', 3)
        self.assertContains(self.response, 'type="password"', 1)

    def test_contains_navigation_links(self):
        dashboard_url = reverse('uid:dashboard')

        self.assertContains(self.response, 'href="{0}"'.format(dashboard_url))
        self.assertContains(self.response, '<button type="submit"')


class UnregisteredAuthViewTest(TestCase):
    """Test that a non register biosample user is redirected to biosample
    registration page"""

    def setUp(self):
        User = get_user_model()

        # create a testuser
        User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        self.client = Client()
        self.client.login(username='test', password='test')

        # this user is not registered in biosample. Get generate token view
        self.url = reverse('biosample:token-generation')
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

    def test_registered(self):
        """A non registered user is redirected to "activate complete"""

        target_url = reverse('accounts:registration_activation_complete')

        self.assertRedirects(self.response, target_url)


class InvalidCreateAuthViewTest(BaseTest):
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


class SuccessFullCreateAuthViewTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        cls.mock_get_patcher = patch('pyUSIrest.auth.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_get_patcher.stop()
        super().tearDownClass()

    def setUp(self):
        # create a test user
        super().setUp()

        # generate tocken
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = generate_token()
        self.mock_get.return_value.status_code = 200

        self.data = {
            'password': 'image-password',
        }

        self.response = self.client.post(self.url, self.data)
        self.dashboard_url = reverse('uid:dashboard')

    def test_redirection(self):
        '''
        A valid form submission should redirect the user to the home page
        '''

        self.assertRedirects(self.response, self.dashboard_url)
        self.check_messages(self.response, "success", "Token generated!")

    def test_next_redirection(self):
        """A valid form submission with a next parameter in request"""

        # construct url
        next_url = reverse("about")
        url = self.url + "?next=%s" % (next_url)

        # get response
        response = self.client.post(url, self.data)

        self.assertRedirects(response, next_url)

    @patch("pyUSIrest.auth.Auth", side_effect=ConnectionError("test"))
    def test_error_with_biosample(self, my_auth):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)

        self.check_messages(
            response,
            "error",
            "Unable to generate token")
