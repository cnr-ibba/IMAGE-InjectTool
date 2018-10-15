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
from ..models import ManagedTeam

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
        submission = Submission.objects.get(pk=self.submission_id)

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


class ManagedTeamMixin():
    """Mixin for teams belonging to user"""

    fixtures = [
        "submissions/user",
        "submissions/dictcountry",
        "submissions/dictrole",
        "submissions/organization",
        "submissions/submission",
        "biosample/account",
        "biosample/managedteam",
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        unmanaged = ManagedTeam.objects.get(pk=2)
        unmanaged.delete()

    def setUp(self):
        # calling my base setup
        super().setUp()

        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can fetch_status
        submission.status = SUBMITTED
        submission.biosample_submission_id = "test-fetch"
        submission.save()

        # track submission ID
        self.submission_id = submission.id

    def common_tests(self, my_auth, my_root, my_team):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = fetch_status()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        self.assertTrue(my_auth.called)
        self.assertTrue(my_root.called)
        self.assertTrue(my_root.return_value.get_team_by_name.called)
        self.assertTrue(my_team.get_submissions.called)


class FetchCompletedTestCase(ManagedTeamMixin, TestCase):
    """a completed submission with two samples"""

    @patch("biosample.tasks.Root")
    @patch("biosample.tasks.get_auth")
    def test_fetch_status(self, my_auth, my_root):
        # mocking chain. The team for test user
        my_team = Mock()
        my_team.name = "subs.test-team-1"

        # a completed submission with two samples
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.submissionStatus = 'Completed'
        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # add submissions to team
        my_team.get_submissions.return_value = [my_submission]

        # passing a list to side effect, I iter throgh mock objects in
        # each mock calls
        my_root.return_value.get_team_by_name.side_effect = [my_team]

        # assert task and mock methods called
        self.common_tests(my_auth, my_root, my_team)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, COMPLETED)


class FetchNotInDBTestCase(ManagedTeamMixin, TestCase):
    """A submission not in db"""

    @patch("biosample.tasks.Root")
    @patch("biosample.tasks.get_auth")
    def test_fetch_status(self, my_auth, my_root):
        # mocking chain. The team for test user
        my_team = Mock()
        my_team.name = "subs.test-team-1"

        # mocking submissions. A submission not in db
        my_submission = Mock()
        my_submission.name = "not-present-in-db"

        # add submissions to team
        my_team.get_submissions.return_value = [my_submission]

        # passing a list to side effect, I iter throgh mock objects in
        # each mock calls
        my_root.return_value.get_team_by_name.side_effect = [my_team]

        # assert task and mock methods called
        self.common_tests(my_auth, my_root, my_team)


class FetchWithErrorsTestCase(ManagedTeamMixin, TestCase):
    """Test a submission with errors for biosample"""

    @patch("biosample.tasks.Root")
    @patch("biosample.tasks.get_auth")
    def test_fetch_status(self, my_auth, my_root):
        # mocking chain. The team for test user
        my_team = Mock()
        my_team.name = "subs.test-team-1"

        # a draft submission with errors
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.submissionStatus = 'Draft'
        my_submission.has_errors.return_value = Counter({True: 1})
        my_submission.get_status.return_value = Counter({'Complete': 1})

        # add submissions to team
        my_team.get_submissions.return_value = [my_submission]

        # passing a list to side effect, I iter throgh mock objects in
        # each mock calls
        my_root.return_value.get_team_by_name.side_effect = [my_team]

        # assert task and mock methods called
        self.common_tests(my_auth, my_root, my_team)

        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, NEED_REVISION)


class FetchDraftTestCase(ManagedTeamMixin, TestCase):
    """a draft submission without errors"""

    @patch("biosample.tasks.Root")
    @patch("biosample.tasks.get_auth")
    def test_fetch_status(self, my_auth, my_root):
        # mocking chain. The team for test user
        my_team = Mock()
        my_team.name = "subs.test-team-1"

        # a draft submission without errors
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.submissionStatus = 'Draft'
        my_submission.has_errors.return_value = Counter({False: 1})
        my_submission.get_status.return_value = Counter({'Complete': 1})

        # add submissions to team
        my_team.get_submissions.return_value = [my_submission]

        # passing a list to side effect, I iter throgh mock objects in
        # each mock calls
        my_root.return_value.get_team_by_name.side_effect = [my_team]

        # assert task and mock methods called
        self.common_tests(my_auth, my_root, my_team)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, SUBMITTED)

        # testing a finalized biosample condition
        self.assertTrue(my_submission.finalize.called)

    @patch("biosample.tasks.Root")
    @patch("biosample.tasks.get_auth")
    def test_fetch_status_pending(self, my_auth, my_root):
        """Testing status with pending validation"""

        # mocking chain. The team for test user
        my_team = Mock()
        my_team.name = "subs.test-team-1"

        # a draft submission without errors
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.submissionStatus = 'Draft'
        my_submission.has_errors.return_value = Counter({False: 1})
        my_submission.get_status.return_value = Counter({'Pending': 1})

        # add submissions to team
        my_team.get_submissions.return_value = [my_submission]

        # passing a list to side effect, I iter throgh mock objects in
        # each mock calls
        my_root.return_value.get_team_by_name.side_effect = [my_team]

        # assert task and mock methods called
        self.common_tests(my_auth, my_root, my_team)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, SUBMITTED)

        # testing a not finalized biosample condition
        self.assertFalse(my_submission.finalize.called)


class FetchWaitingTestCase(ManagedTeamMixin, TestCase):
    """a still running submission"""

    def setUp(self):
        # calling my base setup
        super().setUp()

        # get a submission object
        submission = Submission.objects.get(pk=self.submission_id)

        # change status
        submission.status = WAITING
        submission.save()

    @patch("biosample.tasks.Root")
    @patch("biosample.tasks.get_auth")
    def test_fetch_status(self, my_auth, my_root):
        # mocking chain. The team for test user
        my_team = Mock()
        my_team.name = "subs.test-team-1"

        # a still running submission
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.submissionStatus = 'Draft'

        # add submissions to team
        my_team.get_submissions.return_value = [my_submission]

        # passing a list to side effect, I iter throgh mock objects in
        # each mock calls
        my_root.return_value.get_team_by_name.side_effect = [my_team]

        # assert task and mock methods called
        self.common_tests(my_auth, my_root, my_team)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, WAITING)


class UnManagedTeamMixin():
    """Mixin for teams not belonging to user"""

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        managed = ManagedTeam.objects.get(pk=1)
        managed.delete()

    def common_tests(self, my_auth, my_root, my_team):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = fetch_status()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        self.assertTrue(my_auth.called)
        self.assertTrue(my_root.called)
        self.assertTrue(my_root.return_value.get_team_by_name.called)
        self.assertTrue(my_team.get_submissions.called)


class FetchUnManagedTestCase(ManagedTeamMixin, TestCase):
    """Fetching an unmanaged team"""

    @patch("biosample.tasks.Root")
    @patch("biosample.tasks.get_auth")
    def test_fetch_status(self, my_auth, my_root):
        my_team = Mock()
        my_team.name = "subs.test-team-2"

        # a still running submission
        my_submission = Mock()
        my_submission.name = "not-managed"
        my_submission.submissionStatus = 'Draft'

        # add submissions to team
        my_team.get_submissions.return_value = [my_submission]

        # passing a list to side effect, I iter throgh mock objects in
        # each mock calls
        my_root.return_value.get_team_by_name.side_effect = [my_team]

        # assert task and mock methods called
        self.common_tests(my_auth, my_root, my_team)
