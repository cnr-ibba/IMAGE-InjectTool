#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 16:38:40 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch
from billiard.einfo import ExceptionInfo

from django.core import mail

from common.constants import ERROR
from image_app.models import Submission


class ImportGenericTaskMixinTestCase():
    # the method use for importing data as a string
    upload_method = None
    datasource_type = None

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # setting upload function
        self.my_upload_patcher = patch(self.upload_method)
        self.my_upload = self.my_upload_patcher.start()

        # mocking annotate with zooma function
        self.mock_annotateall_patcher = patch('submissions.tasks.AnnotateAll')
        self.mock_annotateall = self.mock_annotateall_patcher.start()

    def tearDown(self):
        # stopping mock objects
        self.my_upload_patcher.stop()
        self.mock_annotateall_patcher.stop()

        # calling base methods
        super().tearDown()

    def test_on_failure(self):
        """Testing on failure methods"""

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
            "Error in %s loading: Test" % (self.datasource_type))

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in %s loading: %s" % (
                self.datasource_type, self.submission_id),
            email.subject)

        message = 'Error'
        notification_message = 'Error in %s loading: Test' % (
            self.datasource_type)

        self.check_message(message, notification_message)

        # assering zooma not called
        self.assertFalse(self.mock_annotateall.called)

    def test_import_from_file(self):
        """Testing file import"""

        self.my_upload.return_value = True

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert that method were called
        self.assertTrue(self.my_upload.called)

        # assering zooma called
        self.assertTrue(self.mock_annotateall.called)

    def test_import_from_file_errors(self):
        """Testing file import with errors"""

        self.my_upload.return_value = False

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "Error in uploading %s data" % (
            self.datasource_type))

        # assert that method were called
        self.assertTrue(self.my_upload.called)

        # assering zooma not called
        self.assertFalse(self.mock_annotateall.called)
