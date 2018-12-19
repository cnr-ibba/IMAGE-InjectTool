#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 16:05:54 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis

from unittest.mock import Mock, patch

from django.test import Client, TestCase
from django.urls import resolve, reverse
from django.conf import settings
from django.utils import timezone

from image_app.models import Submission, STATUSES
from common.tests import (
        FormMixinTestCase, MessageMixinTestCase, InvalidFormMixinTestCase)

from ..forms import SubmitForm
from ..views import SubmitView

from .session_enabled_test_case import SessionEnabledTestCase
from .test_token import generate_token


# get available status
READY = STATUSES.get_value('ready')
WAITING = STATUSES.get_value('waiting')
ERROR = STATUSES.get_value('error')
SUBMITTED = STATUSES.get_value('submitted')
LOADED = STATUSES.get_value('loaded')
COMPLETED = STATUSES.get_value('completed')


class TestMixin(object):
    """Base class for validation tests"""

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission",
        "biosample/account",
        "biosample/managedteam",
    ]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')


class SubmitViewTest(TestMixin, FormMixinTestCase, TestCase):
    form_class = SubmitForm

    def setUp(self):
        # call base methods
        super(SubmitViewTest, self).setUp()

        # get the url for dashboard
        self.url = reverse('biosample:submit')
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/biosample/submit/')
        self.assertIsInstance(view.func.view_class(), SubmitView)

    def test_form_inputs(self):
        '''
        The view two inputs: csrf, submission_id"
        '''

        # total input is n of form fields + (CSRF)
        self.assertContains(self.response, '<input', 4)
        self.assertContains(self.response, 'type="text"', 1)
        self.assertContains(self.response, 'type="password"', 1)


# --- testing view


class SubmitMixin(TestMixin, MessageMixinTestCase, SessionEnabledTestCase):
    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        cls.redis = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB)

    @classmethod
    def tearDownClass(cls):
        key = "token:submission:1:test"

        if cls.redis.exists(key):
            cls.redis.delete(key)

        super().tearDownClass()

    @patch('biosample.views.SubmitTask.delay')
    def setUp(self, my_submit):
        # call base methods
        super(SubmitMixin, self).setUp()

        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can submit
        submission.status = READY
        submission.save()

        # track submission ID
        self.submission_id = submission.id

        # track owner
        self.owner = submission.owner

        # generate a valid token
        self.generate_token()

        # get the url for dashboard (make request)
        self.url = reverse('biosample:submit')
        self.response = self.client.post(
            self.url, {
                'submission_id': self.submission_id
            }
        )

        # track my patched function
        self.my_submit = my_submit

    def generate_token(self):
        """Placeholder for token generation"""

        self.fail("Please define this method")


class SuccessfulSubmitViewTest(SubmitMixin):
    def generate_token(self):
        """generate a valid token"""
        session = self.get_session()
        session['token'] = generate_token()
        session.save()
        self.set_session_cookies(session)

    def test_redirect(self):
        """test redirection after submission occurs"""

        url = reverse('submissions:detail', kwargs={'pk': self.submission_id})
        self.assertRedirects(self.response, url)

    def test_submit_status(self):
        """check submission to biosample started and submission.state"""

        # check validation started
        self.assertTrue(self.my_submit.called)

        # get submission object
        submission = Submission.objects.get(pk=self.submission_id)

        # check submission.state changed
        self.assertEqual(submission.status, WAITING)
        self.assertEqual(
            submission.message,
            "Waiting for biosample submission")

    def test_valid_token(self):
        """check that a valid token is writtein in redis"""

        key = "token:submission:{submission_id}:{username}".format(
            submission_id=self.submission_id,
            username=self.owner.username)

        self.assertIsNotNone(self.redis.get(key))


# --- issues with token


class NoTokenSubmitViewTest(SubmitMixin):
    """Do a submission without a token"""

    def generate_token(self):
        """remove token from session if present """

        # get session and remove token
        session = self.get_session()

        if 'token' in session:
            del(session['token'])
            session.save()
            self.set_session_cookies(session)

    def test_no_token(self):
        """check no token redirects to form"""

        self.assertEqual(self.response.status_code, 200)

        self.check_messages(
            self.response,
            "error",
            "You haven't generated any token yet")


class ExpiredTokenViewTest(SubmitMixin):
    def generate_token(self):
        """generate an expired token"""

        session = self.get_session()
        now = int(timezone.now().timestamp())
        session['token'] = generate_token(now-10000)
        session.save()
        self.set_session_cookies(session)

    def test_expired_token(self):
        """check that an expired token redirects to form"""

        self.assertEqual(self.response.status_code, 200)

        self.check_messages(
            self.response,
            "error",
            "Your token is expired or near to expire")


class CreateTokenSubmitViewTest(SuccessfulSubmitViewTest):
    """Test that by providing submission id and password I can do a
    submission"""

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        cls.mock_get_patcher = patch('pyUSIrest.auth.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_get_patcher.stop()
        super().tearDownClass()

    @patch('biosample.views.SubmitTask.delay')
    def setUp(self, my_submit):
        """Custom setUp"""

        self.client = Client()
        self.client.login(username='test', password='test')

        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can submit
        submission.status = READY
        submission.save()

        # track submission ID
        self.submission_id = submission.id

        # track owner
        self.owner = submission.owner

        # generate token
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = generate_token()
        self.mock_get.return_value.status_code = 200

        self.data = {
            'password': 'image-password',
            'submission_id': self.submission_id
        }

        # get the url for dashboard (make request)
        self.url = reverse('biosample:submit')
        self.response = self.client.post(self.url, self.data)

        # track my patched function
        self.my_submit = my_submit


class ErrorTokenSubmitViewTest(SubmitMixin):
    @patch("biosample.views.Auth", side_effect=ConnectionError("test"))
    def setUp(self, my_auth):
        """Custom setUp"""

        self.client = Client()
        self.client.login(username='test', password='test')

        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can submit
        submission.status = READY
        submission.save()

        # track submission ID
        self.submission_id = submission.id

        # track owner
        self.owner = submission.owner

        self.data = {
            'password': 'image-password',
            'submission_id': self.submission_id
        }

        # get the url for dashboard (make request)
        self.url = reverse('biosample:submit')
        self.response = self.client.post(self.url, self.data)

        # track my patched function
        self.my_auth = my_auth

    def test_issue_with_biosample(self):
        """check that issues with biosample redirects to form"""

        self.assertEqual(self.response.status_code, 200)

        self.check_messages(
            self.response,
            "error",
            "Unable to generate token")

# --- check status before submission


class NoSubmitViewTest(TestMixin, MessageMixinTestCase, TestCase):
    """No submission if status is not OK"""

    @patch('biosample.views.SubmitTask.delay')
    def setUp(self, my_submit):
        # call base methods
        super(NoSubmitViewTest, self).setUp()

        # get a submission object
        submission = Submission.objects.get(pk=1)

        # track submission ID
        self.submission_id = submission.id

        # set URL
        self.url = reverse('biosample:submit')

        # track my patched function
        self.my_submit = my_submit

    def __common_stuff(self, status):
        """Common function for statuses"""

        # get submission
        submission = Submission.objects.get(pk=self.submission_id)

        # update status and save
        submission.status = status
        submission.save()

        # call valiate views with cyrrent status WAITING
        response = self.client.post(
            self.url, {
                'submission_id': self.submission_id
            }
        )

        # assert redirect
        url = reverse('submissions:detail', kwargs={'pk': self.submission_id})
        self.assertRedirects(response, url)

        # get number of call (equal to first call)
        self.assertEqual(self.my_submit.call_count, 0)

    def test_submission_waiting(self):
        """check no submission with submission status WAITING"""

        # valutate status and no function called
        self.__common_stuff(WAITING)

    def test_submission_error(self):
        """check no submission with submission status ERROR"""

        # valutate status and no function called
        self.__common_stuff(ERROR)

    def test_submission_submitted(self):
        """check no submission with submission status SUBMITTED"""

        # valutate status and no function called
        self.__common_stuff(SUBMITTED)

    def test_submission_completed(self):
        """check no submission with submission status COMPLETED"""

        # valutate status and no function called
        self.__common_stuff(COMPLETED)


# errors with form


class InvalidSubmitViewTest(TestMixin, InvalidFormMixinTestCase, TestCase):
    def setUp(self):
        # call base methods
        super(InvalidSubmitViewTest, self).setUp()

        # get the url for dashboard
        self.url = reverse('biosample:submit')
        self.response = self.client.post(self.url, {})

    def test_status_code(self):
        """Invalid post data returns the form"""

        self.assertEqual(self.response.status_code, 200)


# --- submission owenership


class ErrorSubmitViewtest(TestMixin, TestCase):
    """A class to test submission not belonging to the user or which doesn't
    exists"""

    @patch('biosample.views.SubmitTask.delay')
    def setUp(self, my_submit):
        self.client = Client()
        self.client.login(username='test2', password='test2')

        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can ready
        submission.status = READY
        submission.save()

        # track submission ID
        self.submission_id = submission.id

        # get the url for dashboard
        self.url = reverse('biosample:submit')

        # track my patched function
        self.my_submit = my_submit

    def test_ownership(self):
        """Test a non-owner having a 404 response"""

        response = self.client.post(
            self.url, {
                'submission_id': self.submission_id
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.my_submit.called)

    def test_does_not_exists(self):
        """Test a submission which doesn't exists"""

        response = self.client.post(
            self.url, {
                'submission_id': 99
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.my_submit.called)
