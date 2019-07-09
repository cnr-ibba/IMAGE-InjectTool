#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 11:51:09 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch, Mock
from billiard.einfo import ExceptionInfo

from django.core import mail
from django.test import TestCase

from common.constants import ERROR
from image_app.models import Submission

from .common import BaseExcelMixin
from ..tasks import ImportTemplateTask


class ImportTemplateTaskTest(BaseExcelMixin, TestCase):
    def setUp(self):
        # calling my base class setup
        super().setUp()

        # setting task
        self.my_task = ImportTemplateTask()

    @patch('excel.tasks.send_message_to_websocket')
    @patch('asyncio.get_event_loop')
    def test_on_failure(self, asyncio_mock, send_message_to_websocket_mock):
        """Testing on failure methods"""
        tmp = asyncio_mock.return_value
        tmp.run_until_complete = Mock()

        exc = Exception("Test")
        task_id = "test_task_id"
        args = [self.submission_id]
        kwargs = {}
        einfo = ExceptionInfo

        # call on_failure method
        self.my_task.on_failure(exc, task_id, args, kwargs, einfo)

        # check submission status and message
        submission = Submission.objects.get(pk=self.submission_id)

        # check submission.state changed
        self.assertEqual(submission.status, ERROR)
        self.assertEqual(
            submission.message,
            "Error in Template loading: Test")

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in Template loading: %s" % self.submission_id,
            email.subject)

        self.assertEqual(asyncio_mock.call_count, 1)
        self.assertEqual(tmp.run_until_complete.call_count, 1)
        self.assertEqual(send_message_to_websocket_mock.call_count, 1)
        send_message_to_websocket_mock.assert_called_with(
            {'message': 'Error',
             'notification_message': 'Error in Template loading: Test'}, 1)

    @patch("excel.tasks.upload_template", return_value=True)
    def test_import_from_template(self, my_upload):
        """Testing template import"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert that method were called
        self.assertTrue(my_upload.called)

    @patch("excel.tasks.upload_template", return_value=False)
    def test_import_from_template_errors(self, my_upload):
        """Testing template import with errors"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "Error in uploading Template data")

        # assert that method were called
        self.assertTrue(my_upload.called)
