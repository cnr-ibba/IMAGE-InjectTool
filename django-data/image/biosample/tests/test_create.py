#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 14:55:11 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from django.test import Client, TestCase
from django.urls import resolve, reverse

from uid.models import Organization
from pyUSIrest.auth import Auth

from ..forms import CreateUserForm
from ..views import CreateUserView
from .test_token import generate_token


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
        self.assertEqual(self.response.status_code, 200)

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
        "uid/dictcountry.json",
        "uid/dictrole.json",
        "uid/organization.json"
    ]

    def setUp(self):
        User = get_user_model()

        # create a testuser
        user = User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        # add organization (affiliation) to user
        affiliation = Organization.objects.first()
        user.person.affiliation = affiliation

        # add other infor to user
        user.first_name = "Foo"
        user.last_name = "Bar"

        # saving updated object
        user.save()

        # those will be POST parameters
        self.data = {
            'password1': 'image-password',
            'password2': 'image-password',
        }

        # this is django.test.Client
        self.client = Client()
        self.client.login(username='test', password='test')

        # get the url for dashboard
        self.url = reverse('biosample:create')
        self.response = self.client.get(self.url)

        # patching object
        self.create_user_patcher = patch('pyUSIrest.usi.User.create_user')
        self.create_user = self.create_user_patcher.start()
        self.create_user.return_value = (
            "usr-2a28ca65-2c2f-41e7-9aa5-e829830c6c71")

        def mocked_auth():
            token = generate_token(
                domains=['subs.test-team-1', 'subs.test-team-3'])
            return Auth(token=token)

        self.get_auth_patcher = patch('biosample.views.get_manager_auth')
        self.get_auth = self.get_auth_patcher.start()
        self.get_auth.return_value = mocked_auth()

        self.create_team_patcher = patch('pyUSIrest.usi.User.create_team')
        self.create_team = self.create_team_patcher.start()
        self.create_team.return_value.name = "subs.test-team-3"

        self.get_domain_patcher = patch(
            'pyUSIrest.usi.User.get_domain_by_name')
        self.get_domain = self.get_domain_patcher.start()
        self.get_domain.return_value.domainReference = (
                "dom-41fd3271-d14b-47ff-8de1-e3f0a6d0a693")

        self.add_user_patcher = patch('pyUSIrest.usi.User.add_user_to_team')
        self.add_user = self.add_user_patcher.start()

    def tearDown(self):
        self.create_user_patcher.stop()
        self.get_auth_patcher.stop()
        self.create_team_patcher.stop()
        self.get_domain_patcher.stop()
        self.add_user_patcher.stop()

        super().tearDown()

    def test_deal_with_errors(self):
        """Testing deal with errors method"""

        # change create user reply
        self.create_user.side_effect = ConnectionError("test")

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)

        # assert mail sent
        self.assertGreater(len(mail.outbox), 0)

        self.assertTrue(self.create_user.called)
        self.assertFalse(self.get_auth.called)
        self.assertFalse(self.create_team.called)
        self.assertFalse(self.get_domain.called)
        self.assertFalse(self.add_user.called)

    def test_user_create(self):
        """Testing create user"""

        # posting user and password to generate a new user
        response = self.client.post(self.url, self.data)
        dashboard_url = reverse('uid:dashboard')

        self.assertRedirects(response, dashboard_url)
        self.check_messages(response, "success", "Account created")

        self.assertTrue(self.create_user.called)
        self.assertTrue(self.get_auth.called)
        self.assertTrue(self.create_team.called)
        self.assertTrue(self.get_domain.called)
        self.assertTrue(self.add_user.called)

    def check_message(self, message):
        """assert a non ridirect and a message"""

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.check_messages(response, "error", message)

    def test_error_with_create_user(self):
        """Testing create user with biosample errors"""

        # setting mock objects
        self.create_user.side_effect = ConnectionError("test")

        message = "Problem in creating user"
        self.check_message(message)

        self.assertTrue(self.create_user.called)
        self.assertFalse(self.get_auth.called)
        self.assertFalse(self.create_team.called)
        self.assertFalse(self.get_domain.called)
        self.assertFalse(self.add_user.called)

    def mock_create_team_error(self):
        """Raise a custom exception when creating team"""

        msg = (
            '{"timestamp":1569592802046,"status":500,"error":"Internal Server '
            'Error","exception":"org.springframework.web.client.ResourceAccess'
            'Exception","message":"I/O error on POST request for \"https://'
            'explore.api.aai.ebi.ac.uk/domains/\": No content to map due '
            'to end-of-input\n at [Source: ; line: 1, column: 0]; nested '
            'exception is com.fasterxml.jackson.databind.JsonMappingException:'
            ' No content to map due to end-of-input\n at [Source: ; line: 1, '
            'column: 0]","path":"/api/user/teams"}')

        return ConnectionError(msg)

    def test_error_with_create_team(self):
        """Testing create user"""

        # setting mock objects
        self.create_team.side_effect = self.mock_create_team_error()

        message = "Problem in creating team"
        self.check_message(message)

        self.assertTrue(self.create_user.called)
        self.assertTrue(self.get_auth.called)
        self.assertTrue(self.create_team.called)
        self.assertFalse(self.get_domain.called)
        self.assertFalse(self.add_user.called)

    def test_error_with_add_user_to_team(self):
        """Testing a generic error during user creation step"""

        # setting mock objects
        self.add_user.side_effect = ConnectionError("test")

        message = "Problem in adding user"
        self.check_message(message)

        self.assertTrue(self.create_user.called)
        self.assertTrue(self.get_auth.called)
        self.assertTrue(self.create_team.called)
        self.assertTrue(self.get_domain.called)
        self.assertTrue(self.add_user.called)

    def test_generic_error(self):
        """Testing a generic error during user creation step"""

        # setting mock objects
        self.get_auth.side_effect = ConnectionError("test")

        message = "Problem with EBI-AAP endoints. Please contact IMAGE team"
        self.check_message(message)

        # the first manager auth called is in create user
        self.assertTrue(self.create_user.called)
        self.assertTrue(self.get_auth.called)
        self.assertFalse(self.create_team.called)
        self.assertFalse(self.get_domain.called)
        self.assertFalse(self.add_user.called)


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
        self.assertEqual(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertGreater(len(form.errors), 0)
