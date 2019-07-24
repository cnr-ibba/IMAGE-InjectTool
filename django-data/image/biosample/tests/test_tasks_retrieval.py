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

from ..tasks.retrieval import FetchStatusTask, FetchStatusHelper
from ..models import ManagedTeam, Submission as USISubmission


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


class FetchStatusHelperMixin(FetchMixin):
    """Test class for FetchStatusHelper"""

    fixtures = [
        'biosample/account',
        'biosample/managedteam',
        'biosample/submission',
        'biosample/submissiondata',
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
        self.animal_name = Name.objects.get(pk=3)
        self.sample_name = Name.objects.get(pk=4)

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
        qs = Name.objects.filter(status=COMPLETED)
        self.assertEqual(len(qs), 2)

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
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), self.n_to_submit)


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
