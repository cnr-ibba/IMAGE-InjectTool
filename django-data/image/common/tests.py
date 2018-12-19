#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 10:32:38 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Common tests mixins
"""

import os
import shutil

from django.urls import reverse
from django.test import Client
from django.contrib.messages import get_messages


class LoginMixinTestCase(object):
    url = None

    def test_unathenticated(self):
        '''Non Authenticated user are directed to login page'''

        login_url = reverse("login")
        client = Client()
        response = client.get(self.url)

        self.assertRedirects(
            response, '{login_url}?next={url}'.format(
                login_url=login_url, url=self.url)
        )


class OwnerMixinTestCase(LoginMixinTestCase):
    def test_ownership(self):
        """Test a non-owner having a 404 response"""

        client = Client()
        client.login(username='test2', password='test2')

        response = client.get(self.url)
        self.assertEqual(response.status_code, 404)


class StatusMixinTestCase(object):
    response = None

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)


class MessageMixinTestCase(object):
    def check_messages(self, response, tag, message_text):
        """Check that a response has a message of a certain type"""

        # each element is an instance
        # of django.contrib.messages.storage.base.Message
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        found = False

        # I can have moltiple message, and maybe I need to find a specific one
        for message in all_messages:
            if tag in message.tags and message_text in message.message:
                found = True

        self.assertTrue(found)


class GeneralMixinTestCase(LoginMixinTestCase, StatusMixinTestCase,
                           MessageMixinTestCase):
    pass


class FormMixinTestCase(GeneralMixinTestCase):
    form_class = None

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        if not self.form_class:
            raise Exception("Please set 'form_class' attribute")

        form = self.response.context.get('form')
        self.assertIsInstance(form, self.form_class)


# methods like test_unathenticated need to be called with FormMixinTestCase
class InvalidFormMixinTestCase(StatusMixinTestCase, MessageMixinTestCase):

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertGreater(len(form.errors), 0)


# a mixin to ensure that datasource is in place
class DataSourceMixinTestCase():
    """Place file in data source directory"""

    # class attributes
    uploaded_file = False
    dst_path = None
    model = None

    @classmethod
    def setUpClass(cls):
        """Place test data in data source if needed"""

        # calling my base class setup
        super().setUpClass()

        # ensuring that file cryoweb_test_data_only.sql is present
        submission = cls.model.objects.get(pk=1)
        cls.dst_path = submission.uploaded_file.path

        if not os.path.exists(cls.dst_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            src_path = os.path.join(base_dir, "cryoweb_test_data_only.sql")
            shutil.copy(src_path, cls.dst_path)
            cls.uploaded_file = True

    @classmethod
    def tearDownClass(cls):
        """Remove test data from data source if needed"""

        # remove file if I placed it for tests
        if cls.uploaded_file:
            os.remove(cls.dst_path)

        # calling my base class teardown class
        super().tearDownClass()