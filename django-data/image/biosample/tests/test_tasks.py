#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 14:51:13 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis

from billiard.einfo import ExceptionInfo
from pytest import raises
from collections import Counter
from unittest.mock import patch, Mock

from celery.exceptions import Retry

from django.test import TestCase
from django.conf import settings

from image_app.models import Submission, Person, Name, STATUSES

from ..tasks import submit, fetch_status, get_auth
from .test_token import generate_token
from ..models import ManagedTeam

# get available status
WAITING = STATUSES.get_value('waiting')
LOADED = STATUSES.get_value('loaded')
SUBMITTED = STATUSES.get_value('submitted')
ERROR = STATUSES.get_value('error')
NEED_REVISION = STATUSES.get_value('need_revision')
READY = STATUSES.get_value('ready')
COMPLETED = STATUSES.get_value('completed')


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

        # set status for names, like validation does
        Name.objects.all().update(status=READY)

        # track submission ID
        self.submission_id = submission.id

        # starting mocked objects
        self.mock_root_patcher = patch('biosample.tasks.Root')
        self.mock_root = self.mock_root_patcher.start()

        # start root object
        self.my_root = self.mock_root.return_value

        # mocking chain
        self.my_team = self.my_root.get_team_by_name.return_value
        self.my_team.name = "subs.test-team-1"

        self.my_submission = self.my_team.create_submission.return_value
        self.my_submission.name = "test-submission"

        # mocking get_submission_by_name
        self.my_root.get_submission_by_name.return_value = self.my_submission

    def test_submit(self):
        """Test submitting into biosample"""

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

        # check name status changed
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), 2)

        # assert called mock objects
        self.assertTrue(self.mock_root.called)
        self.assertTrue(self.my_root.get_team_by_name.called)
        self.assertTrue(self.my_team.create_submission.called)
        self.assertFalse(self.my_root.get_submission_by_name.called)
        self.assertEqual(self.my_submission.create_sample.call_count, 2)

    # http://docs.celeryproject.org/en/latest/userguide/testing.html#tasks-and-unit-tests
    @patch("biosample.tasks.submit.retry")
    @patch("biosample.tasks.submit_biosample")
    def test_submit_retry(self, my_submit, my_retry):
        """Test submissions with retry"""

        # Set a side effect on the patched methods
        # so that they raise the errors we want.
        my_retry.side_effect = Retry()
        my_submit.side_effect = ConnectionError()

        with raises(Retry):
            submit(submission_id=1)

    def test_submit_recover(self):
        """Test submission recovering"""

        # update submission object
        submission = Submission.objects.get(pk=self.submission_id)
        submission.biosample_submission_id = "test-submission"
        submission.save()

        # set one name as uploaded
        name = Name.objects.get(name='ANIMAL:::ID:::132713')
        name.status = SUBMITTED
        name.save()

        # calling submit
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
        self.assertEqual(
            submission.biosample_submission_id, "test-submission")

        # check name status changed
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), 2)

        # assert called mock objects
        self.assertTrue(self.mock_root.called)
        self.assertTrue(self.my_root.get_team_by_name.called)
        self.assertFalse(self.my_team.create_submission.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)
        self.assertEqual(self.my_submission.create_sample.call_count, 1)

    def test_on_failure(self):
        """Testing on failure methods"""

        exc = Exception("Test")
        task_id = "test_task_id"
        args = [self.submission_id]
        kwargs = {}
        einfo = ExceptionInfo

        # call on_failure method
        submit.on_failure(exc, task_id, args, kwargs, einfo)

        # check submission status and message
        submission = Submission.objects.get(pk=self.submission_id)

        # check submission.state changed
        self.assertEqual(submission.status, ERROR)
        self.assertEqual(
            submission.message,
            "Error in biosample submission: Test")


class GetAuthTestCase(TestCase):
    @patch("biosample.tasks.Auth")
    def test_get_auth(self, my_auth):
        """Testing get_auth method"""

        get_auth()
        self.assertTrue(my_auth.called)


class FetchMixin():
    """Mixin for fetching status"""

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

        # starting mocked objects
        cls.mock_root_patcher = patch('biosample.tasks.Root')
        cls.mock_root = cls.mock_root_patcher.start()

        cls.mock_auth_patcher = patch('biosample.tasks.get_auth')
        cls.mock_auth = cls.mock_auth_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_root_patcher.stop()
        cls.mock_auth_patcher.stop()

        # calling base method
        super().tearDownClass()

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

        # start root object
        self.my_root = self.mock_root.return_value

    def common_tests(self, my_submission):
        # passing submission to Mocked Root
        self.my_root.get_submission_by_name.return_value = my_submission

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = fetch_status()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        self.assertTrue(self.mock_auth.called)
        self.assertTrue(self.mock_root.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)
        self.assertTrue(my_submission.follow_url.called)


class FetchCompletedTestCase(FetchMixin, TestCase):
    """a completed submission with two samples"""

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

    def test_fetch_status(self):
        # a completed submission with two samples
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.submissionStatus = 'Completed'

        # model follow link to get a document with status 'Completed'
        my_document = Mock()
        my_document.status = 'Completed'
        my_submission.follow_url.return_value = my_document

        # Add samples
        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample1.alias = "animal_1"
        my_sample1.accession = "SAMEA0000001"
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_sample2.alias = "sample_1"
        my_sample2.accession = "SAMEA0000002"
        my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, COMPLETED)

        # check name status changed
        qs = Name.objects.filter(status=COMPLETED)
        self.assertEqual(len(qs), 2)

        # fetch two name objects
        name = Name.objects.get(name='ANIMAL:::ID:::132713')
        self.assertEqual(name.biosample_id, "SAMEA0000001")

        name = Name.objects.get(name='Siems_0722_393449')
        self.assertEqual(name.biosample_id, "SAMEA0000002")

    # http://docs.celeryproject.org/en/latest/userguide/testing.html#tasks-and-unit-tests
    @patch("biosample.tasks.fetch_status.retry")
    @patch("biosample.tasks.fetch_biosample_status")
    def test_fetch_status_retry(self, my_fetch_biosample, my_fetch_status):
        """Test submissions with retry"""

        # Set a side effect on the patched methods
        # so that they raise the errors we want.
        my_fetch_status.side_effect = Retry()
        my_fetch_biosample.side_effect = ConnectionError()

        with raises(Retry):
            fetch_status()


class FetchNotInDBTestCase(FetchMixin, TestCase):
    """A submission not in db"""

    def test_fetch_status(self):
        # mocking submissions. A submission not in db
        my_submission = Mock()
        my_submission.name = "not-present-in-db"

        # assert task and mock methods called
        self.common_tests(my_submission)


class FetchWithErrorsTestCase(FetchMixin, TestCase):
    """Test a submission with errors for biosample"""

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

    def test_fetch_status(self):
        # a draft submission with errors
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.submissionStatus = 'Draft'
        my_submission.has_errors.return_value = Counter({True: 1})
        my_submission.get_status.return_value = Counter({'Complete': 1})

        # model follow link to get a document with status 'Draft'
        my_document = Mock()
        my_document.status = 'Draft'
        my_submission.follow_url.return_value = my_document

        # Add samples
        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample1.alias = "animal_1"
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_sample2.alias = "sample_1"

        # simulate that animal_1 has errors
        my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert submission status
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, NEED_REVISION)

        # check name status changed
        qs = Name.objects.filter(status=NEED_REVISION)
        self.assertEqual(len(qs), 2)


class FetchDraftTestCase(FetchMixin, TestCase):
    """a draft submission without errors"""

    def test_fetch_status(self):
        # a draft submission without errors
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.submissionStatus = 'Draft'
        my_submission.has_errors.return_value = Counter({False: 1})
        my_submission.get_status.return_value = Counter({'Complete': 1})

        # model follow link to get a document with status 'Draft'
        my_document = Mock()
        my_document.status = 'Draft'
        my_submission.follow_url.return_value = my_document

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, SUBMITTED)

        # testing a finalized biosample condition
        self.assertTrue(my_submission.finalize.called)

    def test_fetch_status_pending(self):
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

        # model follow link to get a document with status 'Draft'
        my_document = Mock()
        my_document.status = 'Draft'
        my_submission.follow_url.return_value = my_document

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, SUBMITTED)

        # testing a not finalized biosample condition
        self.assertFalse(my_submission.finalize.called)


class FetchUnsupportedStatusTestCase(FetchMixin, TestCase):
    """A submission with a status I can ignore"""

    def setUp(self):
        # calling my base setup
        super().setUp()

        # a still running submission
        self.my_submission = Mock()
        self.my_submission.name = "test-fetch"

        # passing submission to Mocked Root
        self.my_root.get_submission_by_name.return_value = self.my_submission

    def update_status(self, status):
        # get a submission object
        submission = Submission.objects.get(pk=self.submission_id)

        # change status
        submission.status = status
        submission.save()

    # override FetchMixing methods
    def common_tests(self, status):
        # update submission status
        self.update_status(status)

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = fetch_status()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        self.assertFalse(self.mock_auth.called)
        self.assertFalse(self.mock_root.called)
        self.assertFalse(self.my_root.get_submission_by_name.called)
        self.assertFalse(self.my_submission.follow_url.called)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, status)

    def test_loaded(self):
        """Test fecth_status with a loaded submission"""

        # assert task and mock methods called
        self.common_tests(LOADED)

    def test_need_revision(self):
        """Test fecth_status with a need_revision submission"""

        # assert task and mock methods called
        self.common_tests(NEED_REVISION)

    def test_ready(self):
        """Test fecth_status with a ready submission"""

        # assert task and mock methods called
        self.common_tests(READY)

    def test_completed(self):
        """Test fecth_status with a completed submission"""

        # assert task and mock methods called
        self.common_tests(COMPLETED)
