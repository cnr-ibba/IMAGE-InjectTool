#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 14:51:13 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis
from unittest.mock import patch, Mock

from django.test import TestCase
from django.conf import settings

from image_app.models import Submission

from ..tasks import submit
from .test_token import generate_token

# get available status
READY = Submission.STATUSES.get_value('ready')
SUBMITTED = Submission.STATUSES.get_value('submitted')


class SubmitTestCase(TestCase):
    fixtures = [
        "submissions/user",
        "submissions/dictcountry",
        "submissions/dictrole",
        "submissions/organization",
        "submissions/submission",
        "biosample/account",
        "biosample/managedteam",
    ]

    submission_key = "token:submission:1:test"

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        cls.redis = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB)

        # generate a token
        token = generate_token(domains=['subs.test-team-1'])

        # write token to database
        cls.redis.set(cls.submission_key, token, ex=3600)

    @classmethod
    def tearDownClass(cls):
        if cls.redis.exists(cls.submission_key):
            cls.redis.delete(cls.submission_key)

        super().tearDownClass()

    def setUp(self):
        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can submit
        submission.status = READY
        submission.save()

        # track submission ID
        self.submission_id = submission.id

    # TODO: remove unuseful stuff and test a real case
    @patch("biosample.tasks.Root")
    @patch("biosample.tasks.sleep")
    def test_submit(self, my_sleep, my_root):
        # mocking chain
        my_team = my_root.return_value.get_team_by_name.return_value
        my_team.name = "subs.test-team-1"

        my_submission = my_team.create_submission.return_value
        my_submission.name = "test-submission"

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = submit(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # check submission status and message
        submission = Submission.objects.get(pk=1)

        # check submission.state changed
        self.assertEqual(submission.status, SUBMITTED)
        self.assertEqual(
            submission.message,
            "Waiting for biosample validation")
        self.assertEqual(submission.biosample_submission_id, "test-submission")

        # assert called mock objects
        self.assertTrue(my_root.called)
        self.assertTrue(my_root.return_value.get_team_by_name.called)
        self.assertTrue(my_team.create_submission.called)
