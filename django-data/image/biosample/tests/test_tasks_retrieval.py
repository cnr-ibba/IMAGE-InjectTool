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
from pyUSIrest.exceptions import USIConnectionError

from celery.exceptions import Retry

from django.test import TestCase
from django.core import mail
from django.utils import timezone

from common.constants import (
    LOADED, ERROR, READY, NEED_REVISION, SUBMITTED, COMPLETED, STATUSES)
from common.tests import WebSocketMixin
from uid.models import Submission, Animal, Sample

from ..tasks.retrieval import (
    FetchStatusTask, FetchStatusHelper, RetrievalCompleteTask)
from ..models import ManagedTeam, Submission as USISubmission


class FetchMixin():
    """Mixin for fetching status"""

    fixtures = [
        'biosample/account',
        'biosample/managedteam',
        'biosample/submission',
        'biosample/submissiondata',
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user'
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        unmanaged = ManagedTeam.objects.get(pk=2)
        unmanaged.delete()

        # starting mocked objects
        cls.mock_root_patcher = patch('pyUSIrest.usi.Root')
        cls.mock_root = cls.mock_root_patcher.start()

        cls.mock_auth_patcher = patch('pyUSIrest.auth.Auth')
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
        self.submission_obj.message = "Waiting for biosample validation"
        self.submission_obj.save()

        # set status for objects, like submittask does.
        self.animal_qs = Animal.objects.all()
        self.animal_qs.update(status=SUBMITTED)

        self.sample_qs = Sample.objects.all()
        self.sample_qs.update(status=SUBMITTED)

        # count number of names in UID for such submission (exclude
        # unknown animals)
        self.n_to_submit = self.animal_qs.count() + self.sample_qs.count()

        # track submission ID
        self.submission_obj_id = self.submission_obj.id

        # start root object
        self.my_root = self.mock_root.return_value

    def count_by_status(self, status):
        """Return the number of sample and animal by status"""

        return (
            Animal.objects.filter(status=status).count() +
            Sample.objects.filter(status=status).count()
        )


class FetchStatusHelperMixin(FetchMixin):
    """Test class for FetchStatusHelper"""

    def setUp(self):
        # calling my base setup
        super().setUp()

        # define a biosample submission object
        self.my_submission = Mock()
        self.my_submission.name = "test-fetch"

        # passing submission to Mocked Root
        self.my_root.get_submission_by_name.return_value = self.my_submission

        # get a biosample.model.Submission and update object
        self.usi_submission = USISubmission.objects.get(pk=1)
        self.usi_submission.usi_submission_name = self.my_submission.name
        self.usi_submission.status = SUBMITTED
        self.usi_submission.save()

        # ok setup the object
        self.status_helper = FetchStatusHelper(self.usi_submission)

        # track names
        self.animal_name = Animal.objects.get(pk=1)
        self.sample_name = Sample.objects.get(pk=1)

    def common_tests(self):
        """Assert stuff for each test"""

        # call stuff
        self.status_helper.check_submission_status()

        # UID submission status remain the same
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, SUBMITTED)

        self.assertTrue(self.mock_auth.called)
        self.assertTrue(self.mock_root.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)


class FetchIgnoreTestCase(FetchStatusHelperMixin, TestCase):
    """a submission that could be ignored"""

    def setUp(self):
        # calling my base setup
        super().setUp()

        # an unmanaged status
        self.my_submission.status = 'Unmanaged'

    def common_tests(self, status):
        """Override default common tests. Status is the status the
        submission is supposed to remain"""

        # assert auth, root and get_submission by name called
        super().common_tests()

        # USI submission status did't changed
        self.usi_submission.refresh_from_db()
        self.assertEqual(self.usi_submission.status, status)

        # check animal/sample status didn't changed
        n_to_submit = self.count_by_status(SUBMITTED)
        self.assertEqual(n_to_submit, self.n_to_submit)

    def test_fetch_unmanaged_submission_status(self):
        """Test fetch status for an unmanaged submission"""

        # assert my common tests
        self.common_tests(status=SUBMITTED)

    def test_fetch_not_submitted(self):
        """Ignore a submission with a status different from SUBMITTED"""

        self.usi_submission.status = COMPLETED
        self.usi_submission.save()

        self.common_tests(status=COMPLETED)


class FetchCompletedTestCase(FetchStatusHelperMixin, TestCase):
    """a completed submission with two samples"""

    def setUp(self):
        # calling my base setup
        super().setUp()

        # a completed submission with two samples
        self.my_submission.status = 'Completed'

    def test_fetch_status(self):
        """Test fetch status for a complete submission"""

        # Add samples
        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample1.alias = "IMAGEA000000001"
        my_sample1.accession = "SAMEA0000001"
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_sample2.alias = "IMAGES000000001"
        my_sample2.accession = "SAMEA0000002"
        self.my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # assert auth, root and get_submission by name called
        self.common_tests()

        # USI submission status changed
        self.usi_submission.refresh_from_db()
        self.assertEqual(self.usi_submission.status, COMPLETED)

        # check name status changed
        n_completed = self.count_by_status(COMPLETED)
        self.assertEqual(n_completed, 2)

        # fetch two name objects
        self.animal_name.refresh_from_db()
        self.assertEqual(self.animal_name.biosample_id, "SAMEA0000001")

        self.sample_name.refresh_from_db()
        self.assertEqual(self.sample_name.biosample_id, "SAMEA0000002")

    def test_fetch_status_no_accession(self):
        """Test fetch status for a submission which doens't send accession
        no updates in such case"""

        # Add samples
        my_sample1 = Mock()
        my_sample1.name = "test-animal"
        my_sample1.alias = "IMAGEA000000001"
        my_sample1.accession = None
        my_sample2 = Mock()
        my_sample2.name = "test-sample"
        my_sample2.alias = "IMAGES000000001"
        my_sample2.accession = None
        self.my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # assert auth, root and get_submission by name called
        self.common_tests()

        # USI submission status didn't change
        self.usi_submission.refresh_from_db()
        self.assertEqual(self.usi_submission.status, SUBMITTED)

        # check name status didn't changed
        n_to_submit = self.count_by_status(SUBMITTED)
        self.assertEqual(n_to_submit, self.n_to_submit)


class FetchWithErrorsTestCase(FetchStatusHelperMixin, TestCase):
    """Test a submission with errors for biosample"""

    def setUp(self):
        # calling my base setup
        super().setUp()

        # a draft submission with errors
        self.my_submission.status = 'Draft'
        self.my_submission.has_errors.return_value = Counter(
            {True: 1, False: 1})
        self.my_submission.get_status.return_value = Counter({'Complete': 2})

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
        self.my_submission.get_samples.return_value = [my_sample1, my_sample2]

        # track other objects
        self.my_sample1 = my_sample1
        self.my_sample2 = my_sample2

    def common_tests(self):
        # assert auth, root and get_submission by name called
        super().common_tests()

        # assert custom mock attributes called
        self.assertTrue(self.my_sample1.has_errors.called)
        self.assertTrue(self.my_sample1.get_validation_result.called)

        # if sample has no errors, no all methods will be called
        self.assertTrue(self.my_sample2.has_errors.called)
        self.assertFalse(self.my_sample2.get_validation_result.called)

    def test_fetch_status(self):
        # assert tmock methods called
        self.common_tests()

        # USI submission changed
        self.usi_submission.refresh_from_db()
        self.assertEqual(self.usi_submission.status, NEED_REVISION)

        # check name status changed only for animal (not sample)
        self.animal_name.refresh_from_db()
        self.assertEqual(self.animal_name.status, NEED_REVISION)

        self.sample_name.refresh_from_db()
        self.assertEqual(self.sample_name.status, SUBMITTED)


class FetchDraftTestCase(FetchStatusHelperMixin, TestCase):
    """a draft submission without errors"""

    def common_tests(self):
        # assert auth, root and get_submission by name called
        super().common_tests()

        # USI submission status didn't change
        self.usi_submission.refresh_from_db()
        self.assertEqual(self.usi_submission.status, SUBMITTED)

    def test_fetch_status(self):
        # a draft submission without errors
        self.my_submission.status = 'Draft'
        self.my_submission.has_errors.return_value = Counter({False: 2})
        self.my_submission.get_status.return_value = Counter({'Complete': 2})

        # assert mock methods called
        self.common_tests()

        # testing a finalized biosample condition
        self.assertTrue(self.my_submission.finalize.called)

    def test_fetch_status_pending(self):
        """Testing status with pending validation"""

        # a draft submission without errors
        self.my_submission.status = 'Draft'
        self.my_submission.has_errors.return_value = Counter({False: 2})
        self.my_submission.get_status.return_value = Counter({'Pending': 2})

        # assert mock methods called
        self.common_tests()

        # testing a not finalized biosample condition
        self.assertFalse(self.my_submission.finalize.called)

    def test_fetch_status_submitted(self):
        """Testing status during biosample submission"""

        # a draft submission without errors
        self.my_submission.status = 'Submitted'
        self.my_submission.has_errors.return_value = Counter({False: 2})
        self.my_submission.get_status.return_value = Counter({'Complete': 2})

        # assert mock methods called
        self.common_tests()

        # testing a not finalized biosample condition
        self.assertFalse(self.my_submission.finalize.called)


class FetchLongStatusTestCase(FetchStatusHelperMixin, TestCase):
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
            self.usi_submission.updated_at = testtime
            self.usi_submission.save()

    def common_tests(self):
        # assert auth, root and get_submission by name called
        super().common_tests()

        # biosample.models.Submission status changed
        self.assertEqual(self.usi_submission.status, ERROR)
        self.assertIn(
            "Biosample submission '{}' remained with the same status".format(
                self.my_submission.name),
            self.usi_submission.message
        )

    def test_error_in_submitted_status(self):
        # a still running submission
        self.my_submission.status = 'Submitted'

        # assert mock methods called
        self.common_tests()

    def test_error_in_draft_status(self):
        # a still running submission
        self.my_submission.status = 'Draft'

        # assert mock methods called
        self.common_tests()


class FetchUnsupportedStatusTestCase(FetchMixin, TestCase):
    """A submission object with a status I can ignore. Task will exit
    immediatey"""

    def setUp(self):
        # calling my base setup
        super().setUp()

        # define my task
        self.my_task = FetchStatusTask()

        # change lock_id (useful when running test during cron)
        self.my_task.lock_id = "test-FetchStatusTask"

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


class FetchStatusTaskTestCase(FetchMixin, TestCase):
    def setUp(self):
        # calling my base setup
        super().setUp()

        # set proper status to biosample.models.Submission
        USISubmission.objects.update(status=SUBMITTED)

        # starting mocked objects
        self.mock_helper_patcher = patch(
            'biosample.tasks.retrieval.FetchStatusHelper')
        self.mock_helper = self.mock_helper_patcher.start()

        self.mock_complete_patcher = patch(
            'biosample.tasks.retrieval.RetrievalCompleteTask')
        self.mock_complete = self.mock_complete_patcher.start()

        # define my task
        self.my_task = FetchStatusTask()

        # change lock_id (useful when running test during cron)
        self.my_task.lock_id = "test-FetchStatusTask"

    def tearDown(self):
        self.mock_helper_patcher.stop()
        self.mock_complete_patcher.stop()

        # calling base method
        super().tearDown()

    def test_fetch_status(self):
        """Test fetch status task"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert my objects called
        self.assertTrue(self.mock_helper.called)
        self.assertTrue(self.mock_complete.called)

        # those objects are proper of FetchStatusHelper class, no one
        # call them in this task itself
        self.assertFalse(self.mock_auth.called)
        self.assertFalse(self.mock_root.called)

    def test_fetch_status_all_completed(self):
        """Test fetch status task with completed biosample.models.Submission"""

        # simulate completed case (no more requests to biosample)
        USISubmission.objects.update(status=COMPLETED)

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert no helper called for this submission
        self.assertFalse(self.mock_helper.called)

        # this is called if every submission is completed
        self.assertTrue(self.mock_complete.called)

        # those objects are proper of FetchStatusHelper class, no one
        # call them in this task itself
        self.assertFalse(self.mock_auth.called)
        self.assertFalse(self.mock_root.called)

    # http://docs.celeryproject.org/en/latest/userguide/testing.html#tasks-and-unit-tests
    @patch("biosample.tasks.FetchStatusTask.retry")
    @patch("biosample.tasks.FetchStatusTask.fetch_queryset")
    def test_fetch_status_retry(self, my_fetch, my_retry):
        """Test fetch status with retry"""

        # Set a side effect on the patched methods
        # so that they raise the errors we want.
        my_retry.side_effect = Retry()
        my_fetch.side_effect = USIConnectionError()

        with raises(Retry):
            self.my_task.run()

        self.assertTrue(my_fetch.called)
        self.assertTrue(my_retry.called)

        # assert no helper called for this submission
        self.assertFalse(self.mock_helper.called)
        self.assertFalse(self.mock_complete.called)

    # Test a non blocking instance
    @patch("biosample.tasks.FetchStatusTask.fetch_queryset")
    @patch("redis.lock.Lock.acquire", return_value=False)
    def test_fetch_status_nb(self, my_lock, my_fetch):
        """Test FetchSTatus while a lock is present"""

        res = self.my_task.run()

        # assert database is locked
        self.assertEqual(res, "%s already running!" % (self.my_task.name))
        self.assertFalse(my_fetch.called)

        # assert no helper called for this submission
        self.assertFalse(self.mock_helper.called)
        self.assertFalse(self.mock_complete.called)


class RetrievalCompleteTaskTestCase(FetchMixin, WebSocketMixin, TestCase):
    """testing update status after a fetch status"""

    def setUp(self):
        # calling my base setup
        super().setUp()

        # set proper status to biosample.models.Submission
        USISubmission.objects.update(status=SUBMITTED)

        # define my task
        self.my_task = RetrievalCompleteTask()

    def updated_check(self, status, message):
        """Common check for tests"""

        # set proper status to biosample.models.Submission
        USISubmission.objects.update(status=status, message=message)

        # calling task
        result = self.my_task.run(
            uid_submission_id=self.submission_obj_id)

        # assert a success with data uploading
        self.assertEqual(result, "success")

        # check status and messages
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, status)
        self.assertEqual(self.submission_obj.message, message)

        # calling a WebSocketMixin method
        self.check_message(
            STATUSES.get_value_display(status),
            message)

    def not_updated_check(self, status, message):
        """Test a submission not updated"""

        # set proper status to biosample.models.Submission
        USISubmission.objects.filter(pk=1).update(
            status=status, message=message)

        # calling task
        result = self.my_task.run(
            uid_submission_id=self.submission_obj_id)

        # assert a success with data uploading
        self.assertEqual(result, "success")

        # check status and messages
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, SUBMITTED)
        self.assertEqual(
            self.submission_obj.message,
            "Waiting for biosample validation")

        # defined in websoketmixin
        self.check_message_not_called()

    def test_submitted(self):
        """Test submitted status"""

        status = SUBMITTED
        message = "Waiting for biosample validation"

        self.not_updated_check(
            status,
            message)

    def test_error(self):
        """test an error in a submission"""

        status = ERROR
        message = "error messages"

        self.updated_check(
            status,
            message)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission 1",
            email.subject)

    def test_need_revision(self):
        """test an issue in a submission"""

        status = NEED_REVISION
        message = "error messages"

        self.updated_check(
            status,
            message)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission 1",
            email.subject)

    def test_completed(self):
        """test a submission completed"""

        status = COMPLETED
        message = "completed messages"

        self.updated_check(
            status,
            message)

    def test_partial_submitted(self):
        """Having submitted in statuses will not complete the submission"""

        status = ERROR
        message = "error messages"

        self.not_updated_check(
            status,
            message)

        status = NEED_REVISION
        message = "error messages"

        self.not_updated_check(
            status,
            message)

        status = COMPLETED
        message = "completed messages"

        self.not_updated_check(
            status,
            message)
