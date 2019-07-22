#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 14:51:13 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from pytest import raises
from collections import Counter
from unittest.mock import patch, Mock
from datetime import timedelta

from celery.exceptions import Retry

from django.test import TestCase
from django.core import mail
from django.utils import timezone

from common.constants import (
    LOADED, ERROR, READY, NEED_REVISION, SUBMITTED, COMPLETED)
from common.tests import WebSocketMixin
from image_app.models import Submission, Name

from ..tasks import FetchStatusTask
from ..models import ManagedTeam


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
        self.submission_obj = Submission.objects.get(pk=1)

        # set a status which I can fetch_status
        self.submission_obj.status = SUBMITTED
        self.submission_obj.biosample_submission_id = "test-fetch"
        self.submission_obj.save()

        # set status for names, like submittask does. Only sample not unknown
        # are submitted
        self.name_qs = Name.objects.exclude(name__contains="unknown")
        self.name_qs.update(status=SUBMITTED)

        # count number of names in UID for such submission (exclude
        # unknown animals)
        self.n_to_submit = self.name_qs.count()

        # track submission ID
        self.submission_obj_id = self.submission_obj.id

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


class FetchCompletedTestCase(FetchMixin, WebSocketMixin, TestCase):
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
        my_sample1.alias = "IMAGEA000000001"
        my_sample1.accession = "SAMEA0000001"
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_sample2.alias = "IMAGES000000001"
        my_sample2.accession = "SAMEA0000002"
        my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert status for submissions
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, COMPLETED)

        # check name status changed
        qs = Name.objects.filter(status=COMPLETED)
        self.assertEqual(len(qs), 2)

        # fetch two name objects
        name = Name.objects.get(name='ANIMAL:::ID:::132713')
        self.assertEqual(name.biosample_id, "SAMEA0000001")

        name = Name.objects.get(name='Siems_0722_393449')
        self.assertEqual(name.biosample_id, "SAMEA0000002")

        message = 'Completed'
        notification_message = 'Successful submission into biosample'

        # calling a WebSocketMixin method
        self.check_message(message, notification_message)

    def test_fetch_status_no_accession(self):
        # a completed submission with two samples
        my_submission = Mock()
        my_submission.name = "test-fetch"
        my_submission.status = 'Submitted'

        # Add samples
        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample1.alias = "IMAGEA000000001"
        my_sample1.accession = None
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_sample2.alias = "IMAGES000000001"
        my_sample2.accession = None
        my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # assert task and mock methods called
        self.common_tests(my_submission)

        # assert status for submissions
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, SUBMITTED)

        # check name status changed
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), self.n_to_submit)

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


class FetchWithErrorsTestCase(FetchMixin, WebSocketMixin, TestCase):
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
        my_submission.has_errors.return_value = Counter({True: 1, False: 1})
        my_submission.get_status.return_value = Counter({'Complete': 2})

        # Add samples. Suppose that first failed, second is ok
        my_validation_result1 = Mock()
        my_validation_result1.errorMessages = {
            'Ena': [
                'a sample message',
            ]
        }

        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample1.alias = "IMAGEA000000001"
        my_sample1.has_errors.return_value = True
        my_sample1.get_validation_result.return_value = my_validation_result1

        # sample2 is ok
        my_validation_result2 = Mock()
        my_validation_result2.errorMessages = None

        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_sample2.alias = "IMAGES000000001"
        my_sample2.has_errors.return_value = False
        my_sample2.get_validation_result.return_value = my_validation_result2

        # simulate that IMAGEA000000001 has errors
        my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # track objects
        self.my_submission = my_submission
        self.my_validation_result1 = my_validation_result1
        self.my_validation_result2 = my_validation_result2
        self.my_sample1 = my_sample1
        self.my_sample2 = my_sample2

        # track names
        self.animal_name = Name.objects.get(pk=3)
        self.sample_name = Name.objects.get(pk=4)

    def common_tests(self):
        # assert task and mock methods called
        super().common_tests(self.my_submission)

        # assert custom mock attributes called
        self.assertTrue(self.my_sample1.has_errors.called)
        self.assertTrue(self.my_sample1.get_validation_result.called)

        # if sample has no errors, no all methods will be called
        self.assertTrue(self.my_sample2.has_errors.called)
        self.assertFalse(self.my_sample2.get_validation_result.called)

    def test_fetch_status(self):
        # assert task and mock methods called
        self.common_tests()

        # assert submission status
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, NEED_REVISION)

        # check name status changed only for animal (not sample)
        self.animal_name.refresh_from_db()
        self.assertEqual(self.animal_name.status, NEED_REVISION)

        self.sample_name.refresh_from_db()
        self.assertEqual(self.sample_name.status, SUBMITTED)

        message = 'Need Revision'
        notification_message = 'Error in biosample submission'

        # calling a WebSocketMixin method
        self.check_message(message, notification_message)

    def test_email_sent(self):
        # assert task and mock methods called
        self.common_tests()

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission %s" % self.submission_obj_id,
            email.subject)

        # check for error messages in object
        self.assertIn("a sample message", email.body)

        message = 'Need Revision'
        notification_message = 'Error in biosample submission'

        # calling a WebSocketMixin method
        self.check_message(message, notification_message)


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
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, SUBMITTED)

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
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, SUBMITTED)

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
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, SUBMITTED)

        # testing a not finalized biosample condition
        self.assertFalse(my_submission.finalize.called)


class FetchLongTaskTestCase(FetchMixin, WebSocketMixin, TestCase):
    """A submission wich remain in the same status for a long time"""

    def setUp(self):
        # calling my base setup
        super().setUp()

        # make "now" 2 months ago
        testtime = timezone.now() - timedelta(days=60)

        # https://devblog.kogan.com/blog/testing-auto-now-datetime-fields-in-django
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = testtime

            # update submission updated time with an older date than now
            self.submission_obj.updated_at = testtime
            self.submission_obj.save()

    def test_error_in_submitted_status(self):
        # a still running submission
        self.my_submission = Mock()
        self.my_submission.name = "test-fetch"
        self.my_submission.status = 'Submitted'

        # assert task and mock methods called
        self.common_tests(self.my_submission)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission %s" % self.submission_obj_id,
            email.subject)

        # check submission.state changed
        self.submission_obj.refresh_from_db()

        self.assertEqual(self.submission_obj.status, ERROR)
        self.assertIn(
            "Biosample subission {} remained with the same status".format(
                    self.submission_obj),
            self.submission_obj.message
            )

        message = 'Error'
        notification_message = (
            'Biosample subission Cryoweb '
            '(United Kingdom, test) remained with the '
            'same status for more than 5 days. Please '
            'report it to InjectTool team')

        # calling a WebSocketMixin method
        self.check_message(message, notification_message)

    def test_error_in_draft_status(self):
        # a still running submission
        self.my_submission = Mock()
        self.my_submission.name = "test-fetch"
        self.my_submission.status = 'Draft'

        # assert task and mock methods called
        self.common_tests(self.my_submission)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission %s" % self.submission_obj_id,
            email.subject)

        # check submission.state changed
        self.submission_obj.refresh_from_db()

        self.assertEqual(self.submission_obj.status, ERROR)
        self.assertIn(
            "Biosample subission {} remained with the same status".format(
                    self.submission_obj),
            self.submission_obj.message
            )

        message = 'Error'
        notification_message = (
            'Biosample subission Cryoweb '
            '(United Kingdom, test) remained with the '
            'same status for more than 5 days. Please '
            'report it to InjectTool team')

        # calling a WebSocketMixin method
        self.check_message(message, notification_message)


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
        # change status
        self.submission_obj.status = status
        self.submission_obj.save()

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
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, status)

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
