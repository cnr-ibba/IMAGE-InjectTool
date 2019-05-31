#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:27 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch, Mock
from billiard.einfo import ExceptionInfo

from django.core import mail
from django.test import TestCase

from common.constants import ERROR
from image_app.models import Submission

from .common import BaseTestCase
from ..tasks import ImportCRBAnimTask


class ImportCRBAnimTaskTest(BaseTestCase, TestCase):
    def setUp(self):
        # calling my base class setup
        super().setUp()

        # setting task
        self.my_task = ImportCRBAnimTask()

    @patch('crbanim.tasks.send_message_to_websocket')
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
            "Error in CRBAnim loading: Test")

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in CRBAnim loading: %s" % self.submission_id,
            email.subject)

        self.assertEqual(asyncio_mock.call_count, 1)
        self.assertEqual(tmp.run_until_complete.call_count, 1)
        self.assertEqual(send_message_to_websocket_mock.call_count, 1)
        send_message_to_websocket_mock.assert_called_with('Error', 1)

    @patch("crbanim.tasks.upload_crbanim", return_value=True)
    def test_import_from_crbanim(self, my_upload):
        """Testing crbanim import"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert that method were called
        self.assertTrue(my_upload.called)

    @patch("crbanim.tasks.upload_crbanim", return_value=False)
    def test_import_from_crbanim_errors(self, my_upload):
        """Testing crbianim import with errors"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "Error in uploading CRBAnim data")

        # assert that method were called
        self.assertTrue(my_upload.called)
