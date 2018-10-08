#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:34 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import resolve, reverse

from image_app.models import Submission

from ..forms import ValidateForm
from ..views import ValidateView

# reading statuses
WAITING = Submission.STATUSES.get_value('waiting')


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


class InvalidValidateViewTest(TestMixin, TestCase):
    def setUp(self):
        # call base methods
        super(InvalidValidateViewTest, self).setUp()

        # get the url for dashboard
        self.url = reverse('validation:validate')
        self.response = self.client.post(self.url, {})

    def test_status_code(self):
        """Invalid post data returns the form"""

        print(self.response.content)

        self.assertEqual(self.response.status_code, 200)

    # TODO: check no validation process started

    # TODO: check no validation with submission statuses
