#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 17:24:54 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from image_app.models import Submission, Sample
from common.constants import NEED_REVISION, STATUSES
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

        # setting tasks
        self.my_task = BatchDeleteSamples()

    def test_delete_sample(self):
        sample_ids = ['Siems_0722_393449']

        # calling task and delete a sample
        res = self.my_task.run(
            submission_id=self.submission.id,
            sample_ids=sample_ids)

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
                "samples. Rerun validation please!" % len(sample_ids)))
