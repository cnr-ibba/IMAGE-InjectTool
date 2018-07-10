#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 14:55:11 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os

from decouple import AutoConfig

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse, resolve
from django.conf import settings

from ..forms import CreateUserForm
from ..views import CreateUserView


# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


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


# TODO: test valid user creation, maybe with postman fake responses


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
