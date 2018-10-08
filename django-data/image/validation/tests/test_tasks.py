#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:21 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase

from image_app.models import Submission

from ..tasks import validate_submission

# get available statuses
WAITING = Submission.STATUSES.get_value('waiting')
LOADED = Submission.STATUSES.get_value('loaded')
ERROR = Submission.STATUSES.get_value('error')
READY = Submission.STATUSES.get_value('ready')
NEED_REVISION = Submission.STATUSES.get_value('need_revision')
SUBMITTED = Submission.STATUSES.get_value('submitted')


class ValidateSubmissionTest(TestCase):
    fixtures = [
        "submissions/user",
        "submissions/dictcountry",
        "submissions/dictrole",
        "submissions/organization",
        "submissions/submission"
    ]

    def setUp(self):
        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can validate
        submission.status = LOADED
        submission.save()

        # track submission ID
        self.submission_id = submission.id

    # TODO: remove unuseful stuff and test a real case
    @patch("validation.tasks.sleep")
    def test_validate_submission(self, my_sleep):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = validate_submission(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # TODO: check submission status and message
        submission = Submission.objects.get(pk=1)

        # check submission.state changed
        self.assertEqual(submission.status, READY)
        self.assertEqual(
            submission.message,
            "Submission validated with success")

    def __common_statuses(self, my_sleep):
        """Common function for statuses"""

        res = validate_submission(submission_id=self.submission_id)
        self.assertIn("Can't validate submission", res)
        self.assertEqual(my_sleep.call_count, 0)

    # TODO: remove unuseful stuff and test a real case
    @patch("validation.tasks.sleep")
    def test_submission_waiting(self, my_sleep):
        submission = Submission.objects.get(pk=self.submission_id)
        submission.status = WAITING
        submission.save()

        # check no validation occours
        self.__common_statuses(my_sleep)

    # TODO: remove unuseful stuff and test a real case
    @patch("validation.tasks.sleep")
    def test_submission_error(self, my_sleep):
        submission = Submission.objects.get(pk=self.submission_id)
        submission.status = ERROR
        submission.save()

        # check no validation occours
        self.__common_statuses(my_sleep)

    # TODO: remove unuseful stuff and test a real case
    @patch("validation.tasks.sleep")
    def test_submission_submitted(self, my_sleep):
        submission = Submission.objects.get(pk=self.submission_id)
        submission.status = SUBMITTED
        submission.save()

        # check no validation occours
        self.__common_statuses(my_sleep)
