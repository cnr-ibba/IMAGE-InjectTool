#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 16:05:54 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis

from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import resolve, reverse
from django.conf import settings
from django.contrib.messages import get_messages
from django.utils import timezone

from image_app.models import Submission, STATUSES

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
        "submissions/user",
        "submissions/dictcountry",
        "submissions/dictrole",
        "submissions/organization",
        "submissions/submission",
        "biosample/account",
        "biosample/managedteam",
    ]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')

    def check_messages(self, response, tag, message_text):
        """Check that a response has warnings"""

        # each element is an instance
        # of django.contrib.messages.storage.base.Message
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        found = False

        # I can have moltiple message, and maybe I need to find a specific one
        for message in all_messages:
            if tag in message.tags and message_text in message.message:
                found = True

        self.assertTrue(found)


class SubmitViewTest(TestMixin, TestCase):
    def setUp(self):
        # call base methods
        super(SubmitViewTest, self).setUp()

        # get the url for dashboard
        self.url = reverse('biosample:submit')
        self.response = self.client.get(self.url)

    def test_redirection(self):
        '''Non Authenticated user are directed to login page'''

        login_url = reverse("login")
        client = Client()
        response = client.get(self.url)

        self.assertRedirects(
            response, '{login_url}?next={url}'.format(
                login_url=login_url, url=self.url)
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_url_resolves_view(self):
        view = resolve('/biosample/submit/')
        self.assertIsInstance(view.func.view_class(), SubmitView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')

        self.assertIsInstance(form, SubmitForm)

    def test_form_inputs(self):
        '''
        The view two inputs: csrf, submission_id"
        '''

        # total input is n of form fields + (CSRF)
        self.assertContains(self.response, '<input', 2)


class SuccessfulSubmitViewTest(TestMixin, SessionEnabledTestCase):
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

    @patch('biosample.views.submit.delay')
    def setUp(self, my_submit):
        # call base methods
        super(SuccessfulSubmitViewTest, self).setUp()

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
        session = self.get_session()
        session['token'] = generate_token()
        session.save()
        self.set_session_cookies(session)

        # get the url for dashboard (make request)
        self.url = reverse('biosample:submit')
        self.response = self.client.post(
            self.url, {
                'submission_id': self.submission_id
            }
        )

        # track my patched function
        self.my_submit = my_submit

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

    def __common_redirect(self):
        """Common stuff called when there are problems with tocken"""

        # get submission object
        submission = Submission.objects.get(pk=self.submission_id)

        # set a status which I can submit
        submission.status = READY
        submission.save()

        # make request
        self.response = self.client.post(
            self.url, {
                'submission_id': self.submission_id
            }
        )

        # assert a redirect
        next_url = reverse('biosample:token-generation') + "?next=%s" % (
            reverse('submissions:detail', kwargs={'pk': self.submission_id}))
        self.assertRedirects(self.response, next_url)

    def test_no_token(self):
        """check no token redirects to token:generate"""

        # get session and remove token
        session = self.get_session()
        del(session['token'])
        session.save()
        self.set_session_cookies(session)

        # test redirect to token generation
        self.__common_redirect()

        self.check_messages(
            self.response,
            "error",
            "You haven't generated any token yet")

    def test_expired_token(self):
        """check that an expired token redirects to token:generate"""

        session = self.get_session()
        now = int(timezone.now().timestamp())
        session['token'] = generate_token(now-10000)
        session.save()
        self.set_session_cookies(session)

        # test redirect to token generation
        self.__common_redirect()

        self.check_messages(
            self.response,
            "error",
            "Your token is expired or near to expire")


class NoSubmitViewTest(TestMixin, TestCase):
    """No submission if status is not OK"""

    @patch('biosample.views.submit.delay')
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


class InvalidSubmitViewTest(TestMixin, TestCase):
    def setUp(self):
        # call base methods
        super(InvalidSubmitViewTest, self).setUp()

        # get the url for dashboard
        self.url = reverse('biosample:submit')
        self.response = self.client.post(self.url, {})

    def test_status_code(self):
        """Invalid post data returns the form"""

        self.assertEqual(self.response.status_code, 200)
