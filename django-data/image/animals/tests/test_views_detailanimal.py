#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 13:52:26 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.tests import MessageMixinTestCase
from uid.models import Animal

from ..views import DetailAnimalView
from .common import AnimalFeaturesMixin, AnimalViewTestMixin


class DetailAnimalViewTest(
        AnimalViewTestMixin, TestCase):

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('animals:detail', kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/animals/1/')
        self.assertIsInstance(view.func.view_class(), DetailAnimalView)

    def test_edit_not_found_status_code(self):
        url = reverse('submissions:edit', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_contains_navigation_links(self):
        """Contain links to ListAnimalView, EditAnimalView DeleteAnimalView
        and SubmissionEditView"""

        animal_list_url = reverse('animals:list')
        submission_edit_url = reverse('submissions:detail', kwargs={'pk': 1})
        animal_update_url = reverse('animals:update', kwargs={'pk': 1})
        animal_delete_url = reverse('animals:delete', kwargs={'pk': 1})

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    animal_list_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    submission_edit_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    animal_update_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    animal_delete_url))


class DetailAnimalViewMessagesTest(
        AnimalFeaturesMixin, MessageMixinTestCase, TestCase):
    """Test messages in DetailAnimalView"""

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('animals:detail', kwargs={'pk': 1})

        # get an animal object
        animal = Animal.objects.get(pk=1)

        # get validation result
        self.validationresult = animal.name.validationresult

    def check_message(self, message_type, message_str):
        """Test messages in DetailAnimalView"""

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
        """Test info message in DetailAnimalView"""

        # define a info string
        message_str = "Info: test"
        self.check_message('info', message_str)

    def test_warning_message(self):
        """Test warning message in DetailAnimalView"""

        # define a warning string
        message_str = "Warning: test"
        self.check_message('warning', message_str)

    def test_error_message(self):
        """Test error message in DetailAnimalView"""

        # define a error string
        message_str = "Error: test"
        self.check_message('error', message_str)

        # another error string
        message_str = "test"
        self.check_message('error', message_str)
