#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 11:08:12 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import Client, TestCase
from django.urls import resolve, reverse

from common.constants import LOADED, SUBMITTED, COMPLETED, ERROR
from image_app.models import Submission
from common.tests import GeneralMixinTestCase, OwnerMixinTestCase

from ..views import DetailSubmissionView


class DetailSubmissionViewTest(
        GeneralMixinTestCase, OwnerMixinTestCase, TestCase):

    """Test Submission DetailView"""

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission"
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('submissions:detail', kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/')
        self.assertIsInstance(view.func.view_class(), DetailSubmissionView)

    def test_new_not_found_status_code(self):
        url = reverse('submissions:detail', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_ownership(self):
        """Test ownership for a submissions"""

        client = Client()
        client.login(username='test2', password='test2')

        response = client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_contains_navigation_links(self):
        """test links for data edit, validate and submit"""

        # HINT: button unactive class is renderd by template and template_tags
        edit_url = reverse('submissions:edit', kwargs={'pk': 1})
        validate_url = ("javascript:{document.getElementById('validate')."
                        "submit()}")
        submit_url = "javascript:{document.getElementById('submit').submit()}"
        list_url = reverse('submissions:list')
        dashboard_url = reverse('image_app:dashboard')
        reload_url = reverse('submissions:reload', kwargs={'pk': 1})

        self.assertContains(self.response, 'href="{0}"'.format(edit_url))
        self.assertContains(self.response, 'href="{0}"'.format(validate_url))
        self.assertContains(self.response, 'href="{0}"'.format(submit_url))
        self.assertContains(self.response, 'href="{0}"'.format(list_url))
        self.assertContains(self.response, 'href="{0}"'.format(dashboard_url))
        self.assertContains(self.response, 'href="{0}"'.format(reload_url))

        # check template form parameters
        param = '<input type="hidden" name="submission_id" value="1"'
        self.assertContains(self.response, param, count=2)

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
        submission.status = LOADED
        submission.message = "import complete"
        submission.save()

        # get a new response
        response = self.client.get(self.url)

        self.check_messages(
            response,
            "info",
            "import complete")

    def test_submitted(self):
        """With submitted data into biosample (not yet finalized) I will get
        an error message"""

        # set loaded flag
        submission = Submission.objects.get(pk=1)
        submission.status = SUBMITTED
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
        submission.status = COMPLETED
        submission.message = "Successful submission into biosample"
        submission.save()

        # get a new response
        response = self.client.get(self.url)

        # check message
        self.check_messages(
            response,
            "info",
            "Successful submission into biosample")

    # simulate errors in uploading data
    def test_errors(self):
        # set loaded flag
        submission = Submission.objects.get(pk=1)
        submission.message = "Fake Error"
        submission.status = ERROR
        submission.save()

        # get a new response
        response = self.client.get(self.url)

        self.check_messages(
            response,
            "error",
            "Fake Error")
