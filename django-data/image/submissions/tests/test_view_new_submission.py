#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 16:58:41 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.urls import reverse, resolve
from django.test import Client, TestCase

from image_app.models import User

from ..views import CreateSubmissionView
from ..forms import SubmissionForm


class Initialize(TestCase):
    """Does the common stuff when testing cases are run"""

    def setUp(self):
        # create a testuser
        User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('submissions:create')
        self.response = self.client.get(self.url)


class CreateSubmissionViewTest(Initialize):
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
        self.assertEquals(self.response.status_code, 200)

    def test_url_resolves_view(self):
        view = resolve('/submissions/create/')
        self.assertIsInstance(view.func.view_class(), CreateSubmissionView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, SubmissionForm)

    def test_form_inputs(self):

        # total input is n of form fields + (CSRF) + file
        self.assertContains(self.response, '<input', 6)
        self.assertContains(self.response, 'type="text"', 4)
        self.assertContains(self.response, 'type="file"', 1)
        self.assertContains(self.response, '<select', 2)


class SuccessfulCreateSubmissionViewTest(Initialize):
    pass


class InvalidCreateSubmissionViewTest(Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # submit an empty dictionary
        self.response = self.client.post(self.url, {})

    def test_signup_status_code(self):
        '''
        An invalid form submission should return to the same page
        '''
        self.assertEquals(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertGreater(len(form.errors), 0)
