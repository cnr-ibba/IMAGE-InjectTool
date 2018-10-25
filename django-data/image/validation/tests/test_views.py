#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:34 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import resolve, reverse

from image_app.models import Submission, STATUSES

from ..forms import ValidateForm
from ..views import ValidateView

# reading statuses
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
        "submissions/submission"
    ]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')


class ValidateViewTest(TestMixin, TestCase):
    def setUp(self):
        # call base methods
        super(ValidateViewTest, self).setUp()

        # get the url for dashboard
        self.url = reverse('validation:validate')
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
        view = resolve('/validation/validate')
        self.assertIsInstance(view.func.view_class(), ValidateView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')

        self.assertIsInstance(form, ValidateForm)

    def test_form_inputs(self):
        '''
        The view two inputs: csrf, submission_id"
        '''

        # total input is n of form fields + (CSRF)
        self.assertContains(self.response, '<input', 2)


class SuccessfulValidateViewTest(TestMixin, TestCase):
    @patch('validation.views.validate_submission.delay')
    def setUp(self, my_validation):
        # call base methods
        super(SuccessfulValidateViewTest, self).setUp()

        # get a submission object
        submission = Submission.objects.get(pk=1)

        # set a status which I can validate
        submission.status = LOADED
        submission.save()

        # track submission ID
        self.submission_id = submission.id

        # get the url for dashboard
        self.url = reverse('validation:validate')
        self.response = self.client.post(
            self.url, {
                'submission_id': self.submission_id
            }
        )

        # track my patched function
        self.my_validation = my_validation

    def test_redirect(self):
        """test redirection after validation occurs"""

        url = reverse('submissions:detail', kwargs={'pk': self.submission_id})
        self.assertRedirects(self.response, url)

    def test_validation_status(self):
        """check validation started and submission.state"""

        # check validation started
        self.assertTrue(self.my_validation.called)

        # get submission object
        submission = Submission.objects.get(pk=self.submission_id)

        # check submission.state changed
        self.assertEqual(submission.status, WAITING)
        self.assertEqual(
            submission.message,
            "waiting for data validation")


class NoValidateViewTest(TestMixin, TestCase):
    @patch('validation.views.validate_submission.delay')
    def setUp(self, my_validation):
        # call base methods
        super(NoValidateViewTest, self).setUp()

        # get a submission object
        submission = Submission.objects.get(pk=1)

        # track submission ID
        self.submission_id = submission.id

        # get the url for dashboard
        self.url = reverse('validation:validate')

        # track my patched function
        self.my_validation = my_validation

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
        self.assertEqual(self.my_validation.call_count, 0)

    def test_submission_waiting(self):
        """check no validation with submission status WAITING"""

        # valutate status and no function called
        self.__common_stuff(WAITING)

    def test_submission_error(self):
        """check no validation with submission status ERROR"""

        # valutate status and no function called
        self.__common_stuff(ERROR)

    def test_submission_submitted(self):
        """check no validation with submission status SUBMITTED"""

        # valutate status and no function called
        self.__common_stuff(SUBMITTED)

    def test_submission_completed(self):
        """check no validation with submission status COMPLETED"""

        # valutate status and no function called
        self.__common_stuff(COMPLETED)


class InvalidValidateViewTest(TestMixin, TestCase):
    @patch('validation.views.validate_submission.delay')
    def setUp(self, my_validation):
        # call base methods
        super(InvalidValidateViewTest, self).setUp()

        # get the url for dashboard
        self.url = reverse('validation:validate')
        self.response = self.client.post(self.url, {})

        # track my patched function
        self.my_validation = my_validation

    def test_status_code(self):
        """Invalid post data returns the form"""

        self.assertEqual(self.response.status_code, 200)

    def test_novalidation(self):
        """check no validation process started"""

        self.assertFalse(self.my_validation.called)
