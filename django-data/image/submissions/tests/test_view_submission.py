#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 11:08:12 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import resolve, reverse

from image_app.models import Submission, STATUSES

from ..views import DetailSubmissionView


class DetailSubmissionViewTest(TestCase):
    """Test Submission DetailView"""

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission"
    ]

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
        self.assertEqual(self.response.status_code, 200)

    def test_ownership(self):
        """Test a non-owner having a 404 response"""

        client = Client()
        client.login(username='test2', password='test2')

        response = client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/')
        self.assertIsInstance(view.func.view_class(), DetailSubmissionView)

    def test_new_not_found_status_code(self):
        url = reverse('submissions:detail', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # TODO: test links for data edit, validate and submit

    # simulate data loaded and unloaded with messages
    def test_unloaded(self):
        self.check_messages(
            self.response,
            "warning",
            "waiting for data loading")

    def test_loaded(self):
        """If data were loaded, no warning messages are present"""

        # set loaded flag
        submission = Submission.objects.get(pk=1)
        submission.status = STATUSES.get_value('loaded')
        submission.save()

        # get a new response
        response = self.client.get(self.url)

        # get all response
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        self.assertTrue(len(all_messages) == 0)

    def test_submitted(self):
        """With submitted data into biosample (not yet finalized) I will get
        an error message"""

        # set loaded flag
        submission = Submission.objects.get(pk=1)
        submission.status = STATUSES.get_value('submitted')
        submission.message = "submitted"
        submission.save()

        # get a new response
        response = self.client.get(self.url)

        self.check_messages(
            response,
            "warning",
            "submitted")

    def test_completed(self):
        """If submission is completed (submitted and finalized in biosample)
        no warning messages are present"""

        # set loaded flag
        submission = Submission.objects.get(pk=1)
        submission.status = STATUSES.get_value('completed')
        submission.save()

        # get a new response
        response = self.client.get(self.url)

        # get all response
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        self.assertTrue(len(all_messages) == 0)

    # simulate errors in uploading data
    def test_errors(self):
        # set loaded flag
        submission = Submission.objects.get(pk=1)
        submission.message = "Fake Error"
        submission.status = STATUSES.get_value('error')
        submission.save()

        # get a new response
        response = self.client.get(self.url)

        self.check_messages(
            response,
            "error",
            "Fake Error")
