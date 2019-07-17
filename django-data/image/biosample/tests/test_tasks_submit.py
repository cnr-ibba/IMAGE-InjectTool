#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 10:51:40 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase

from common.constants import READY, COMPLETED

from .common import SubmitMixin
from ..models import Submission as USISubmission, SubmissionData
from ..tasks import SplitSubmissionTask


class SplitSubmissionTaskTestCase(SubmitMixin, TestCase):
    def setUp(self):
        # call Mixin method
        super().setUp()

        # setting tasks
        self.my_task = SplitSubmissionTask()

        # patching objects
        self.mock_chord_patcher = patch('biosample.tasks.submit.chord')
        self.mock_chord = self.mock_chord_patcher.start()

        self.mock_submit_patcher = patch('biosample.tasks.submit.submit')
        self.mock_submit = self.mock_submit_patcher.start()

        self.mock_complete_patcher = patch(
            'biosample.tasks.submit.submissioncomplete')
        self.mock_complete = self.mock_complete_patcher.start()

    def tearDown(self):
        # stopping mock objects
        self.mock_chord_patcher.stop()
        self.mock_submit_patcher.stop()
        self.mock_complete_patcher.stop()

        # calling base object
        super().tearDown()

    # ovverride MAX_SAMPLES in order to split data
    @patch('biosample.tasks.submit.MAX_SAMPLES', 2)
    def test_split_submission(self):
        """Test splitting submission data"""

        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # get usi_submission qs
        usi_submissions_qs = USISubmission.objects.all()

        # asserting two biosample.submission data objects
        self.assertEqual(usi_submissions_qs.count(), 2)

        # assert two data for each submission
        for usi_submission in usi_submissions_qs:
            self.assertEqual(usi_submission.status, READY)

            # grab submission data queryset
            submission_data_qs = SubmissionData.objects.filter(
                submission=usi_submission)
            self.assertEqual(submission_data_qs.count(), 2)

            for submission_data in submission_data_qs:
                self.assertEqual(submission_data.status, READY)

    # ovverride MAX_SAMPLES in order to split data
    @patch('biosample.tasks.submit.MAX_SAMPLES', 2)
    def test_split_submission_partial(self):
        """Test splitting submission data with some data already submitted"""

        self.name_qs.filter(pk__in=[3, 4]).update(status=COMPLETED)

        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # get usi_submission qs
        usi_submissions_qs = USISubmission.objects.all()

        # asserting one biosample.submission data object
        self.assertEqual(usi_submissions_qs.count(), 1)

        # assert two data for each submission
        for usi_submission in usi_submissions_qs:
            self.assertEqual(usi_submission.status, READY)

            # grab submission data queryset
            submission_data_qs = SubmissionData.objects.filter(
                submission=usi_submission)
            self.assertEqual(submission_data_qs.count(), 2)

            for submission_data in submission_data_qs:
                self.assertEqual(submission_data.status, READY)
