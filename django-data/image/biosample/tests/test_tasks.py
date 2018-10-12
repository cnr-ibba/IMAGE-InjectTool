#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 14:51:13 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis

from collections import Counter
from unittest.mock import patch, Mock

from django.test import TestCase
from django.conf import settings

from image_app.models import Submission, Person

from ..tasks import submit, fetch_status, get_auth
from .test_token import generate_token

# get available status
SUBMITTED = Submission.STATUSES.get_value('submitted')
NEED_REVISION = Submission.STATUSES.get_value('need_revision')
COMPLETED = Submission.STATUSES.get_value('completed')
WAITING = Submission.STATUSES.get_value('waiting')
READY = Submission.STATUSES.get_value('ready')


class SubmitTestCase(TestCase):
    fixtures = [
        "submissions/user",
        "submissions/dictcountry",
        "submissions/dictrole",
        "submissions/organization",
        "submissions/submission",
        "biosample/account",
        "biosample/managedteam",
        "image_app/dictsex",
        "image_app/dictspecie",
        "image_app/dictbreed",
        "image_app/name",
        "image_app/animal",
        "image_app/sample"
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

        # now fix person table
        person = Person.objects.get(user__username="test")
        person.affiliation_id = 1
        person.role_id = 1
        person.initials = "T"
        person.save()

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

    @patch("biosample.tasks.Root")
    def test_submit(self, my_root):
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
        self.assertEqual(my_submission.create_sample.call_count, 2)


class GetAuthTestCase(TestCase):
    @patch("biosample.tasks.Auth")
    def test_get_auth(self, my_auth):
        """Testing get_auth method"""

        get_auth()
        self.assertTrue(my_auth.called)


class FetchStatusTestCase(TestCase):
    fixtures = [
        "submissions/user",
        "submissions/dictcountry",
        "submissions/dictrole",
        "submissions/organization",
        "submissions/submission",
        "biosample/account",
        "biosample/managedteam",
    ]

    def setUp(self):
        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can fetch_status
        submission.status = SUBMITTED
        submission.biosample_submission_id = "test-submission1"
        submission.datasource_version = submission.biosample_submission_id
        submission.save()

        # duplicating objects: https://stackoverflow.com/a/4736172/4385116
        submission = Submission.objects.get(pk=1)
        submission.pk = 3
        submission.biosample_submission_id = "test-submission3"
        submission.datasource_version = submission.biosample_submission_id
        submission.save()

        submission = Submission.objects.get(pk=1)
        submission.pk = 4
        submission.biosample_submission_id = "test-submission4"
        submission.datasource_version = submission.biosample_submission_id
        submission.save()

        submission = Submission.objects.get(pk=1)
        submission.status = WAITING
        submission.pk = 5
        submission.biosample_submission_id = "test-submission5"
        submission.datasource_version = submission.biosample_submission_id
        submission.save()

        # track submission ID
        self.submission_id = submission.id

    @patch("biosample.tasks.Root")
    @patch("biosample.tasks.get_auth")
    def test_fetch_status(self, my_auth, my_root):
        # mocking chain. The team for test user
        my_team1 = Mock()
        my_team1.name = "subs.test-team-1"

        # a completed submission with two samples
        my_submission1 = Mock()
        my_submission1.name = "test-submission1"
        my_submission1.submissionStatus = 'Completed'
        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_submission1.get_samples.return_value = [my_sample1, my_sample2]

        # mocking submissions. A submission not in db
        my_submission2 = Mock()
        my_submission2.name = "not-present-in-db"

        # a draft submission with errors
        my_submission3 = Mock()
        my_submission3.name = "test-submission3"
        my_submission3.submissionStatus = 'Draft'
        my_submission3.has_errors.return_value = Counter({True: 1})

        # a draft submission without errors
        my_submission4 = Mock()
        my_submission4.name = "test-submission4"
        my_submission4.submissionStatus = 'Draft'
        my_submission4.has_errors.return_value = Counter({False: 1})

        # a still running submission
        my_submission5 = Mock()
        my_submission5.name = "test-submission5"
        my_submission5.submissionStatus = 'Draft'

        # add submissions to team
        my_team1.get_submissions.return_value = [
            my_submission1, my_submission2, my_submission3, my_submission4,
            my_submission5]

        # a managed team not own by the test user
        my_team2 = Mock()
        my_team2.name = "subs.test-team-2"
        my_team2.get_submissions.return_value = []

        # passing a list to side effect, I iter throgh mock objects in
        # each mock calls
        my_root.return_value.get_team_by_name.side_effect = [
            my_team1, my_team2]

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = fetch_status()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert status for submissions
        submission = Submission.objects.get(pk=1)
        self.assertEqual(submission.status, COMPLETED)

        submission = Submission.objects.get(pk=3)
        self.assertEqual(submission.status, NEED_REVISION)

        submission = Submission.objects.get(pk=5)
        self.assertEqual(submission.status, WAITING)

        # assert called mock objects
        self.assertTrue(my_auth.called)
        self.assertTrue(my_root.called)
        self.assertTrue(my_root.return_value.get_team_by_name.called)
        self.assertTrue(my_team1.get_submissions.called)
