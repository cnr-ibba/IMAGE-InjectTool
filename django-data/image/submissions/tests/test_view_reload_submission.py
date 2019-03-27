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

import common
from common.tests import (
    FormMixinTestCase, OwnerMixinTestCase, InvalidFormMixinTestCase,
    DataSourceMixinTestCase, MessageMixinTestCase, StatusMixinTestCase)
from common.constants import (
    CRB_ANIM_TYPE, CRYOWEB_TYPE, TEMPLATE_TYPE, ERROR, WAITING)
from image_app.models import Submission

from ..views import ReloadSubmissionView
from ..forms import ReloadForm


class TestBase(DataSourceMixinTestCase, TestCase):
    # define attribute in DataSourceMixinTestCase
    model = Submission

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission"
    ]

    data_sources_paths = {
        CRYOWEB_TYPE: "cryoweb_test_data_only.sql",
        CRB_ANIM_TYPE: "crbanim_test_data.csv",
        TEMPLATE_TYPE: "crbanim_test_data.csv"  # point this to a real template
    }

    def setUp(self):
        # call base method
        super().setUp()

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('submissions:reload', kwargs={'pk': 1})

    def get_data(self, ds_type=CRYOWEB_TYPE):
        """Get data dictionary"""

        # get data source path relying on type
        ds_path = os.path.join(
            common.tests.__path__[0],
            self.data_sources_paths[ds_type]
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


class SuccessfulReloadMixin(StatusMixinTestCase):
    def tearDown(self):
        if hasattr(self, "submission"):
            # read written file
            self.submission.refresh_from_db()

            # delete uploaded file if exists
            fullpath = self.submission.uploaded_file.path

            if os.path.exists(fullpath):
                os.remove(fullpath)

        # call super method
        super().tearDown()

    def test_redirect(self):
        url = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertRedirects(self.response, url)

    def test_task_called(self):
        self.assertTrue(self.my_task.called)

    def test_submission_status(self):
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, WAITING)
        self.assertEqual(
            self.submission.message,
            "waiting for data loading")


class SuccessfulReloadSubmissionViewTest(
        SuccessfulReloadMixin, OwnerMixinTestCase, TestBase):
    # patch to simulate data load
    @patch('cryoweb.tasks.import_from_cryoweb.delay')
    def setUp(self, my_task):
        # call base method
        super().setUp()

        # this post request create a new data_source file
        self.response = self.client.post(
            self.url,
            self.get_data(),
            follow=True)

        # setting task
        self.my_task = my_task

        # get submission, with the new data_source file
        self.submission = Submission.objects.get(pk=1)


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


class CRBAnimReloadSubmissionViewTest(
        SuccessfulReloadMixin, TestBase):

    @patch('submissions.views.ImportCRBAnimTask.delay')
    def setUp(self, my_task):
        # call base method
        super().setUp()

        # get a submission object
        self.submission = Submission.objects.get(pk=1)

        # change template type
        self.submission.datasource_type = CRB_ANIM_TYPE
        self.submission.save()

        # this post request create a new data_source file
        self.response = self.client.post(
            self.url,
            self.get_data(ds_type=CRB_ANIM_TYPE),
            follow=True)

        # track task
        self.my_task = my_task


class TemplateReloadSubmissionViewTest(
        StatusMixinTestCase, MessageMixinTestCase, TestBase):
    def setUp(self):
        # call base method
        super().setUp()

        # get a submission object
        self.submission = Submission.objects.get(pk=1)

        # change template type
        self.submission.datasource_type = TEMPLATE_TYPE
        self.submission.save()

        # this post request create a new data_source file
        self.response = self.client.post(
            self.url,
            self.get_data(ds_type=TEMPLATE_TYPE),
            follow=True)

    def tearDown(self):
        if hasattr(self, "submission"):
            # read written file
            self.submission.refresh_from_db()

            # delete uploaded file if exists
            fullpath = self.submission.uploaded_file.path

            if os.path.exists(fullpath):
                os.remove(fullpath)

        # call super method
        super().tearDown()

    def test_message(self):
        self.check_messages(
            self.response,
            "error",
            "Template reload is not implemented")

    def test_redirect(self):
        url = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertRedirects(self.response, url)

    def test_error_in_submission(self):
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, ERROR)
        self.assertEqual(
            self.submission.message,
            "Template reload is not implemented")
