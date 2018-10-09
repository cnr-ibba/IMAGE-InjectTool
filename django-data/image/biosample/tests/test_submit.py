#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 16:05:54 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import resolve, reverse

from image_app.models import Submission

from ..forms import SubmitForm
from ..views import SubmitView

# get available status
READY = Submission.STATUSES.get_value('ready')
WAITING = Submission.STATUSES.get_value('waiting')
ERROR = Submission.STATUSES.get_value('error')
SUBMITTED = Submission.STATUSES.get_value('submitted')
LOADED = Submission.STATUSES.get_value('loaded')
COMPLETED = Submission.STATUSES.get_value('completed')


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


class SuccessfulSubmitViewTest(TestMixin, TestCase):
    @patch('biosample.views.submit.delay')
    def setUp(self, my_submit):
        # call base methods
        super(SuccessfulSubmitViewTest, self).setUp()

        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can validate
        submission.status = READY
        submission.save()

        # track submission ID
        self.submission_id = submission.id

        # get the url for dashboard
        self.url = reverse('biosample:submit')
        self.response = self.client.post(
            self.url, {
                'submission_id': self.submission_id
            }
        )

        # track my patched function
        self.my_submit = my_submit

    def test_redirect(self):
        """test redirection after validation occurs"""

        url = reverse('submissions:detail', kwargs={'pk': self.submission_id})
        self.assertRedirects(self.response, url)

    def test_validation_status(self):
        """check validation started and submission.state"""

        # check validation started
        self.assertTrue(self.my_submit.called)

        # get submission object
        submission = Submission.objects.get(pk=self.submission_id)

        # check submission.state changed
        self.assertEqual(submission.status, WAITING)
        self.assertEqual(
            submission.message,
            "Waiting for biosample submission")


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
