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
from unittest.mock import patch, Mock, PropertyMock

from celery.exceptions import Retry

from django.test import TestCase
from django.conf import settings
from django.core import mail

from image_app.models import Submission, Name

from ..tasks import SubmitTask, FetchStatusTask
from ..models import ManagedTeam

from .common import (
    SubmitMixin, SUBMITTED, ERROR, COMPLETED, NEED_REVISION, LOADED, READY,
    generate_token)


class SubmitTestCase(SubmitMixin, TestCase):

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
        # call Mixin emthod
        super().setUp()

        # setting tasks
        self.my_task = SubmitTask()

    def test_submit(self):
        """Test submitting into biosample"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission_obj.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission_obj.status, SUBMITTED)
        self.assertEqual(
            self.submission_obj.message,
            "Waiting for biosample validation")
        self.assertEqual(
            self.submission_obj.biosample_submission_id,
            "new-submission")

        # check name status changed
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), 2)

        # assert called mock objects
        self.assertTrue(self.mock_root.called)
        self.assertTrue(self.my_root.get_team_by_name.called)
        self.assertTrue(self.my_team.create_submission.called)
        self.assertFalse(self.my_root.get_submission_by_name.called)
        self.assertEqual(self.new_submission.create_sample.call_count, 2)
        self.assertFalse(self.new_submission.propertymock.called)

    # http://docs.celeryproject.org/en/latest/userguide/testing.html#tasks-and-unit-tests
    @patch("biosample.tasks.SubmitTask.retry")
    @patch("biosample.tasks.SubmitTask.submit_biosample")
    def test_submit_retry(self, my_submit, my_retry):
        """Test submissions with retry"""

        # Set a side effect on the patched methods
        # so that they raise the errors we want.
        my_retry.side_effect = Retry()
        my_submit.side_effect = ConnectionError()

        with raises(Retry):
            self.my_task.run(submission_id=1)

        self.assertTrue(my_submit.called)
        self.assertTrue(my_retry.called)

    def test_submit_recover(self):
        """Test submission recovering"""

        # update submission object
        self.submission_obj.biosample_submission_id = "test-submission"
        self.submission_obj.save()

        # set one name as uploaded
        name = Name.objects.get(name='ANIMAL:::ID:::132713')
        name.status = SUBMITTED
        name.save()

        # calling submit
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # reload submission
        self.submission_obj.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission_obj.status, SUBMITTED)
        self.assertEqual(
            self.submission_obj.message,
            "Waiting for biosample validation")

        # check name status changed
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), 2)

        # assert called mock objects
        self.assertTrue(self.mock_root.called)
        self.assertFalse(self.my_root.get_team_by_name.called)
        self.assertFalse(self.my_team.create_submission.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)
        self.assertEqual(self.my_submission.create_sample.call_count, 1)
        self.assertTrue(self.my_submission.propertymock.called)

    def test_submit_no_recover(self):
        """Test submission recovering with a closed submission"""

        # update submission status
        self.my_submission.propertymock = PropertyMock(
            return_value='Completed')
        type(self.my_submission).status = self.my_submission.propertymock

        # update submission object
        self.submission_obj.biosample_submission_id = "test-submission"
        self.submission_obj.save()

        # calling submit
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # reload submission
        self.submission_obj.refresh_from_db()

        # check submission.state changed
        self.assertEqual(
            self.submission_obj.biosample_submission_id,
            "new-submission")
        self.assertEqual(self.submission_obj.status, SUBMITTED)
        self.assertEqual(
            self.submission_obj.message,
            "Waiting for biosample validation")

        # check name status changed
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), 2)

        # assert called mock objects
        self.assertTrue(self.mock_root.called)
        self.assertTrue(self.my_root.get_team_by_name.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)
        self.assertTrue(self.my_team.create_submission.called)
        self.assertFalse(self.my_submission.create_sample.called)
        self.assertEqual(self.new_submission.create_sample.call_count, 2)
        self.assertTrue(self.my_submission.propertymock.called)
        self.assertFalse(self.new_submission.propertymock.called)

    def test_submit_patch(self):
        """Test patching submission"""

        # creating mock samples
        my_samples = [
            Mock(**{'alias': 'animal_1',
                    'title': 'a 4-year old pig organic fed'}),
            Mock(**{'alias': 'sample_1',
                    'title': 'semen collected when the animal turns to 4'}),
        ]

        # mocking set samples
        self.my_submission.get_samples.return_value = my_samples

        # update submission object
        self.submission_obj.biosample_submission_id = "test-submission"
        self.submission_obj.save()

        # calling submit
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # reload submission
        self.submission_obj.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission_obj.status, SUBMITTED)
        self.assertEqual(
            self.submission_obj.message,
            "Waiting for biosample validation")

        # check name status changed
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), 2)

        # assert called mock objects
        self.assertTrue(self.mock_root.called)
        self.assertFalse(self.my_root.get_team_by_name.called)
        self.assertFalse(self.my_team.create_submission.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)
        self.assertEqual(self.my_submission.create_sample.call_count, 0)
        self.assertTrue(self.my_submission.propertymock.called)

        # testing patch
        for sample in my_samples:
            self.assertTrue(sample.patch.called)

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
            "Error in biosample submission: Test")

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission %s" % self.submission_id,
            email.subject)


class FetchMixin():
    """Mixin for fetching status"""

    fixtures = [
        'biosample/account',
        'biosample/managedteam',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/organization',
        'image_app/submission',
        'image_app/user'
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        unmanaged = ManagedTeam.objects.get(pk=2)
        unmanaged.delete()

        # starting mocked objects
        cls.mock_root_patcher = patch('pyUSIrest.client.Root')
        cls.mock_root = cls.mock_root_patcher.start()

        cls.mock_auth_patcher = patch('biosample.helpers.Auth')
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

        # set status for names, like submittask does. Only sample not unknown
        # are submitted
        Name.objects.exclude(name__contains="unknown").update(status=SUBMITTED)

        # track submission ID
        self.submission_id = submission.id

        # start root object
        self.my_root = self.mock_root.return_value

        # define my task
        self.my_task = FetchStatusTask()

        # change lock_id (useful when running test during cron)
        self.my_task.lock_id = "test-FetchStatusTask"

    def common_tests(self, my_submission):
        # passing submission to Mocked Root
        self.my_root.get_submission_by_name.return_value = my_submission

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        self.assertTrue(self.mock_auth.called)
        self.assertTrue(self.mock_root.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)


class FetchCompletedTestCase(FetchMixin, TestCase):
    """a completed submission with two samples"""

    fixtures = [
        'biosample/account',
        'biosample/managedteam',
        'image_app/animal',
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
        'image_app/name',
        'image_app/organization',
        'image_app/publication',
        'image_app/sample',
        'image_app/submission',
        'image_app/user'
    ]

    def test_fetch_status(self):
        # a completed submission with two samples
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.status = 'Completed'

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

    def test_fetch_status_no_accession(self):
        # a completed submission with two samples
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.status = 'Submitted'

        # Add samples
        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample1.alias = "animal_1"
        my_sample1.accession = None
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_sample2.alias = "sample_1"
        my_sample2.accession = None
        my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, SUBMITTED)

        # check name status changed
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), 2)

    # http://docs.celeryproject.org/en/latest/userguide/testing.html#tasks-and-unit-tests
    @patch("biosample.tasks.FetchStatusTask.retry")
    @patch("biosample.tasks.FetchStatusTask.fetch_queryset")
    def test_fetch_status_retry(self, my_fetch, my_retry):
        """Test fetch status with retry"""

        # Set a side effect on the patched methods
        # so that they raise the errors we want.
        my_retry.side_effect = Retry()
        my_fetch.side_effect = ConnectionError()

        with raises(Retry):
            self.my_task.run()

        self.assertTrue(my_fetch.called)
        self.assertTrue(my_retry.called)

    # Test a non blocking instance
    @patch("biosample.tasks.FetchStatusTask.fetch_queryset")
    @patch("redis.lock.Lock.acquire", return_value=False)
    def test_fetch_status_nb(self, my_lock, my_fetch):
        """Test FetchSTatus while a lock is present"""

        res = self.my_task.run()

        # assert database is locked
        self.assertEqual(res, "%s already running!" % (self.my_task.name))
        self.assertFalse(my_fetch.called)


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
        'biosample/account',
        'biosample/managedteam',
        'image_app/animal',
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
        'image_app/name',
        'image_app/organization',
        'image_app/publication',
        'image_app/sample',
        'image_app/submission',
        'image_app/user'
    ]

    def setUp(self):
        # calling my base setup
        super().setUp()

        # a draft submission with errors
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.status = 'Draft'
        my_submission.has_errors.return_value = Counter({True: 1})
        my_submission.get_status.return_value = Counter({'Complete': 1})

        # Add samples
        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample1.alias = "animal_1"
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_sample2.alias = "sample_1"

        # simulate that animal_1 has errors
        my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # track object
        self.my_submission = my_submission

    def test_fetch_status(self):
        # assert task and mock methods called
        self.common_tests(self.my_submission)

        # assert submission status
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, NEED_REVISION)

        # check name status changed
        qs = Name.objects.filter(status=NEED_REVISION)
        self.assertEqual(len(qs), 2)

    def test_email_sent(self):
        # assert task and mock methods called
        self.common_tests(self.my_submission)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission %s" % self.submission_id,
            email.subject)


class FetchDraftTestCase(FetchMixin, TestCase):
    """a draft submission without errors"""

    def test_fetch_status(self):
        # a draft submission without errors
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.status = 'Draft'
        my_submission.has_errors.return_value = Counter({False: 1})
        my_submission.get_status.return_value = Counter({'Complete': 1})

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, SUBMITTED)

        # testing a finalized biosample condition
        self.assertTrue(my_submission.finalize.called)

    def test_fetch_status_pending(self):
        """Testing status with pending validation"""

        # a draft submission without errors
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.status = 'Draft'
        my_submission.has_errors.return_value = Counter({False: 1})
        my_submission.get_status.return_value = Counter({'Pending': 1})

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, SUBMITTED)

        # testing a not finalized biosample condition
        self.assertFalse(my_submission.finalize.called)

    def test_fetch_status_submitted(self):
        """Testing status during biosample submission"""

        # a draft submission without errors
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.status = 'Submitted'
        my_submission.has_errors.return_value = Counter({False: 1})
        my_submission.get_status.return_value = Counter({'Complete': 1})

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert status for submissions
        submission = Submission.objects.get(pk=self.submission_id)
        self.assertEqual(submission.status, SUBMITTED)

        # testing a not finalized biosample condition
        self.assertFalse(my_submission.finalize.called)


class FetchUnsupportedStatusTestCase(FetchMixin, TestCase):
    """A submission object with a status I can ignore"""

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
        res = self.my_task.run()

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
