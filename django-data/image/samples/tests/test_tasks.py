#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 17:24:54 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from billiard.einfo import ExceptionInfo

from django.core import mail
from django.test import TestCase

from image_app.models import Submission, Sample
from common.constants import NEED_REVISION, STATUSES, ERROR
from common.tests import WebSocketMixin

from .common import SampleFeaturesMixin
from ..tasks import BatchDeleteSamples


class BatchDeleteSamplesTest(
        SampleFeaturesMixin, WebSocketMixin, TestCase):

    def setUp(self):
        # calling base methods
        super().setUp()

        # get a submission object
        self.submission = Submission.objects.get(pk=1)
        self.submission_id = self.submission.id

        # setting samples to delete
        self.sample_ids = ['Siems_0722_393449']

        # setting tasks
        self.my_task = BatchDeleteSamples()

    def test_on_failure(self):
        """Testing on failure methods"""

        exc = Exception("Test")
        task_id = "test_task_id"
        args = []
        kwargs = {
            'submission_id': self.submission_id,
            'animal_ids': self.sample_ids}
        einfo = ExceptionInfo

        # call on_failure method
        self.my_task.on_failure(exc, task_id, args, kwargs, einfo)

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, ERROR)
        self.assertEqual(
            self.submission.message,
            "Error in sample batch delete: Test")

        # test email sent
        self.assertGreater(len(mail.outbox), 0)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in sample batch delete for submission: 1",
            email.subject)

        self.check_message(
            message='Error',
            notification_message='Error in sample batch delete: Test')

    def test_delete_sample(self):
        # calling task and delete a sample
        res = self.my_task.run(
            submission_id=self.submission.id,
            sample_ids=self.sample_ids)

        self.assertEqual(res, "success")

        # no samples
        n_samples = Sample.objects.count()
        self.assertEqual(n_samples, 0)

        # updating validation messages

        # calling a WebSocketMixin method
        # no validation message since no data in validation table
        self.check_message(
            message=STATUSES.get_value_display(NEED_REVISION),
            notification_message=(
                "You've removed %s "
                "samples. Rerun validation please!" % len(self.sample_ids)))

    def test_delete_samples_not_exists(self):
        # calling task and delete a animal
        res = self.my_task.run(
            submission_id=self.submission_id,
            sample_ids=["meow"])

        self.assertEqual(res, "success")

        # all samples remain
        n_samples = Sample.objects.count()
        self.assertEqual(n_samples, 1)

        # updating validation messages

        # calling a WebSocketMixin method
        # no validation message since no data in validation table
        self.check_message(
            message=STATUSES.get_value_display(NEED_REVISION),
            notification_message=(
                "You've removed 0 samples. It wasn't possible to find records "
                "with these ids: meow. Rerun validation please!")
        )
