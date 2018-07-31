#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 11:08:12 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.urls import resolve, reverse
from django.test import TestCase, Client

from ..views import DetailSubmissionView


class DeatilSubmissionViewTest(TestCase):
    """Does the common stuff when testing cases are run"""

    fixtures = [
        "submissions/user",
        "submissions/dictcountry",
        "submissions/submission"
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('submissions:detail', kwargs={'pk': 1})
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
        self.assertEquals(self.response.status_code, 200)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/')
        self.assertIsInstance(view.func.view_class(), DetailSubmissionView)

    # TODO: test links for data edit, validate and submit
