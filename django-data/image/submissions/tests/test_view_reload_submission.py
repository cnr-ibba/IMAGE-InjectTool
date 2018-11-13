#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 16:35:48 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os

from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.tests import (
    FormMixinTestCase, OwnerMixinTestCase, InvalidFormMixinTestCase)
import common

from ..views import ReloadSubmissionView
from ..forms import ReloadForm


class TestBase(TestCase):
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

        self.url = reverse('submissions:reload', kwargs={'pk': 1})

    def get_data(self):
        """Get data dictionary"""

        # get data source path
        ds_path = os.path.join(
            common.__path__[0],
            "cryoweb_test_data_only.sql"
        )

        # define test data
        data = {
            'uploaded_file': open(ds_path),
            'agree_reload': True
        }

        return data


class ReloadSubmissionViewTest(
        FormMixinTestCase, OwnerMixinTestCase, TestBase):

    form_class = ReloadForm

    def setUp(self):
        # call base method
        super().setUp()

        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/reload/')
        self.assertIsInstance(view.func.view_class(), ReloadSubmissionView)

    def test_form_inputs(self):

        # total input is n of form fields + (CSRF) + 1 file + 1 checkbox
        self.assertContains(self.response, '<input', 3)
        self.assertContains(self.response, 'type="file"', 1)
        self.assertContains(self.response, 'type="checkbox"', 1)

    def test_reload_not_found_status_code(self):
        url = reverse('submissions:reload', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_contains_navigation_links(self):
        """Contain links to DetailSubmissionView"""

        link = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertContains(self.response, 'href="{0}"'.format(link))


class SuccessfulReloadSubmissionViewTest(OwnerMixinTestCase, TestBase):
    # patch to simulate data load
    @patch('cryoweb.tasks.import_from_cryoweb.delay')
    def setUp(self, my_task):
        # call base method
        super().setUp()

        self.response = self.client.post(self.url, self.get_data())
        self.my_task = my_task

    def test_redirect(self):
        url = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertRedirects(self.response, url)

    def test_task_called(self):
        self.assertTrue(self.my_task.called)


class InvalidReloadSubmissionViewTest(
        InvalidFormMixinTestCase, OwnerMixinTestCase, TestBase):

    # patch to simulate data load
    @patch('cryoweb.tasks.import_from_cryoweb.delay')
    def setUp(self, my_task):
        # call base method
        super().setUp()

        self.response = self.client.post(self.url, {})
        self.my_task = my_task

    def test_task_called(self):
        self.assertFalse(self.my_task.called)
