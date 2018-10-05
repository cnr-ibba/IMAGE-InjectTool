#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:34 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import resolve, reverse

from ..forms import ValidateForm
from ..views import ValidateView


class TestMixin(object):
    """Base class for validation tests"""
    def setUp(self):
        User = get_user_model()

        # create a testuser
        self.user = User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

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
    # TODO: test redirection after validation occurs
    # TODO: check validation started
    # TODO: check submission.state changed
    pass


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
