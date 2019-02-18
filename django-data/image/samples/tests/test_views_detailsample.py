#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 13:52:26 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.tests import MessageMixinTestCase
from image_app.models import Sample
from validation.models import ValidationResult

from ..views import DetailSampleView
from .common import SampleFeaturesMixin, SampleViewTestMixin


class DetailSampleViewTest(
        SampleViewTestMixin, TestCase):

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('samples:detail', kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/samples/1/')
        self.assertIsInstance(view.func.view_class(), DetailSampleView)

    def test_edit_not_found_status_code(self):
        url = reverse('submissions:edit', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_contains_navigation_links(self):
        """Contain links to ListSampleView, EditSampleView DeleteSampleView
        and SubmissionEditView"""

        sample_list_url = reverse('samples:list')
        submission_edit_url = reverse('submissions:detail', kwargs={'pk': 1})
        sample_update_url = reverse('samples:update', kwargs={'pk': 1})
        sample_delete_url = reverse('samples:delete', kwargs={'pk': 1})

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    sample_list_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    submission_edit_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    sample_update_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    sample_delete_url))


class DetailSampleViewMessagesTest(
        SampleFeaturesMixin, MessageMixinTestCase, TestCase):
    """Test messages in DetailSampleView"""

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('samples:detail', kwargs={'pk': 1})

        # get an sample object
        sample = Sample.objects.get(pk=1)

        # set validation result (since is not present in features)
        validation = ValidationResult()
        validation.status = "Pass"
        sample.name.validationresult = validation
        sample.name.save()

        self.validationresult = validation

    def check_message(self, message_type, message_str):
        """Test messages in DetailSampleView"""

        self.validationresult.messages = [message_str]
        self.validationresult.save()

        # get the page
        response = self.client.get(self.url)

        # check messages (defined in common.tests.MessageMixinTestCase
        self.check_messages(
            response,
            message_type,
            message_str)

    def test_info_message(self):
        """Test info message in DetailSampleView"""

        # define a info string
        message_str = "Info: test"
        self.check_message('info', message_str)

    def test_warning_message(self):
        """Test warning message in DetailSampleView"""

        # define a warning string
        message_str = "Warning: test"
        self.check_message('warning', message_str)

    def test_error_message(self):
        """Test error message in DetailSampleView"""

        # define a error string
        message_str = "Error: test"
        self.check_message('error', message_str)

        # another error string
        message_str = "test"
        self.check_message('error', message_str)
