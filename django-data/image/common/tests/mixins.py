#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 14:34:02 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import shutil

from unittest.mock import patch, Mock

from django.urls import reverse
from django.test import Client
from django.contrib.messages import get_messages

from ..constants import LOADED, ERROR


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
class DataSourceMixinTestCase(object):
    """Place file in data source directory"""

    # class attributes
    uploaded_file = False
    dst_path = None
    submission_model = None
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # the method is use to upload data into database
    upload_method = None

    @classmethod
    def setUpClass(cls):
        """Place test data in data source if needed"""

        # calling my base class setup
        super().setUpClass()

        # ensuring that file cryoweb_test_data_only.sql is present
        submission = cls.submission_model.objects.get(pk=1)
        cls.dst_path = submission.uploaded_file.path

        # get datasource filename from submission object
        datasource_filename = os.path.basename(submission.uploaded_file.path)

        if not os.path.exists(cls.dst_path):
            src_path = os.path.join(cls.base_dir, datasource_filename)
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

    def upload_datasource(self, message):
        """Testing uploading and importing data from crbanim to UID"""

        # assert upload
        self.assertTrue(self.upload_method(self.submission))

        # reload submission
        self.submission.refresh_from_db()

        # assert submission messages
        self.assertEqual(
            self.submission.status,
            LOADED)

        self.assertIn(
            message,
            self.submission.message)

    def check_errors(self, my_check, message):
        """Common stuff for error in file loading"""

        self.assertFalse(self.upload_method(self.submission))

        # reload submission
        self.submission.refresh_from_db()

        # test my mock method called
        self.assertTrue(my_check.called)

        self.assertEqual(
            self.submission.status,
            ERROR)

        # check for two distinct messages
        self.assertIn(
            message,
            self.submission.message)

        self.assertNotIn(
            "import completed for submission",
            self.submission.message)


# TODO: move into submission.tests (since related to submission.helpers)
class WebSocketMixin(object):
    """Override setUp to mock websocket objects"""

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # setting channels methods
        self.asyncio_mock_patcher = patch(
            'asyncio.get_event_loop')
        self.asyncio_mock = self.asyncio_mock_patcher.start()

        # mocking asyncio return value
        self.run_until = self.asyncio_mock.return_value
        self.run_until.run_until_complete = Mock()

        # another patch
        self.send_msg_ws_patcher = patch(
            'submissions.helpers.send_message_to_websocket')
        self.send_msg_ws = self.send_msg_ws_patcher.start()

    def tearDown(self):
        # stopping mock objects
        self.asyncio_mock_patcher.stop()
        self.send_msg_ws_patcher.stop()

        # calling base methods
        super().tearDown()

    def check_message(
            self, message, notification_message, validation_message=None,
            pk=1):
        """assert message to websocket called with parameters"""

        # construct message according parameters
        message = {
            'message': message,
            'notification_message': notification_message
        }

        # in case of successful data upload, a validation message is sent
        if validation_message:
            message['validation_message'] = validation_message

        self.assertEqual(self.asyncio_mock.call_count, 1)
        self.assertEqual(self.run_until.run_until_complete.call_count, 1)
        self.assertEqual(self.send_msg_ws.call_count, 1)
        self.send_msg_ws.assert_called_with(
            message,
            pk)

    def check_message_not_called(self):
        """Check django channels async messages not called"""

        self.assertEqual(self.asyncio_mock.call_count, 0)
        self.assertEqual(self.run_until.run_until_complete.call_count, 0)
        self.assertEqual(self.send_msg_ws.call_count, 0)
