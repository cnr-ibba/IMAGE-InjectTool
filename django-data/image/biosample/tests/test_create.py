#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 14:55:11 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch, Mock

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse, resolve

from image_app.models import Organization

from ..forms import CreateUserForm
from ..views import CreateUserView


class Basetest(TestCase):
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
        self.url = reverse('biosample:create')
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


class CreateUserViewTest(Basetest):
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
        view = resolve('/biosample/create/')
        self.assertIsInstance(view.func.view_class(), CreateUserView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')

        self.assertIsInstance(form, CreateUserForm)

    def test_form_inputs(self):
        '''
        The view must contain eleven inputs: csrf, username, first_name,
        last_name, email, password1, password2, affiliation, role,
        organization and agree_gdpr checkbox
        '''

        # total input is n of form fields + (CSRF)
        self.assertContains(self.response, '<input', 3)
        self.assertContains(self.response, 'type="password"', 2)


class SuccessfulCreateUserViewTest(Basetest):
    fixtures = [
        "dictcountry.json", "dictrole.json", "organization.json"
    ]

    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyEBIrest.client.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_post_patcher = patch('pyEBIrest.client.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()
        cls.mock_get_patcher.stop()

    def setUp(self):
        User = get_user_model()

        # create a testuser
        user = User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        # add organization to user
        organization = Organization.objects.first()
        user.person.organization = organization
        user.save()

        self.client = Client()
        self.client.login(username='test', password='test')

        # get the url for dashboard
        self.url = reverse('biosample:create')
        self.response = self.client.get(self.url)

    def mocked_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = "Not implemented: %s" % (args[0])

            def json(self):
                return self.json_data

        return MockResponse(None, 404)

    def mocked_post(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = "Not implemented: %s" % (args[0])

            def json(self):
                return self.json_data

        return MockResponse(None, 404)

    @patch('requests.post', side_effect=mocked_post)
    @patch('requests.get', side_effect=mocked_get)
    def test_user_create(self, mock_get, mock_post):
        """Testing create user"""

        self.data = {
            'password1': 'image-password',
            'password2': 'image-password',
        }

        response = self.client.post(self.url, self.data)
        dashboard_url = reverse('image_app:dashboard')

        self.assertRedirects(response, dashboard_url)
        self.check_messages(response, "success", "Account created")


class InvalidCreateUserViewTests(Basetest):
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
