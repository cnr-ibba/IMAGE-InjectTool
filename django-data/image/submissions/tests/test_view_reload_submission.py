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
    FormMixinTestCase, OwnerMixinTestCase, InvalidFormMixinTestCase,
    StatusMixinTestCase)
from common.constants import (
    CRB_ANIM_TYPE, CRYOWEB_TYPE, TEMPLATE_TYPE, WAITING)
from uid.models import Submission
from uid.tests import DataSourceMixinTestCase

from .common import SubmissionFormMixin
from ..views import ReloadSubmissionView
from ..forms import ReloadForm


class TestBase(SubmissionFormMixin, DataSourceMixinTestCase, TestCase):
    fixtures = [
        "uid/user",
        "uid/dictcountry",
        "uid/dictrole",
        "uid/organization",
        "uid/submission"
    ]

    def setUp(self):
        # call base method
        super().setUp()

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('submissions:reload', kwargs={'pk': 1})

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

    def get_data(self, ds_file=CRYOWEB_TYPE):
        """Get data dictionary"""

        ds_type, ds_path = super().get_data(ds_file)

        # define test data
        data = {
            'uploaded_file': open(ds_path, "rb"),
            'datasource_type': ds_type,
            'datasource_version': "reload",
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
        # +1 select + text
        self.assertContains(self.response, '<input', 4)
        self.assertContains(self.response, '<select', 1)
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
    @patch('submissions.views.ImportCryowebTask.delay')
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
    @patch('submissions.views.ImportCryowebTask.delay')
    def setUp(self, my_task):
        # call base method
        super().setUp()

        self.response = self.client.post(self.url, {})
        self.my_task = my_task

    def test_task_called(self):
        self.assertFalse(self.my_task.called)


class ReloadValidationTest(TestBase):
    def common_check(self, response, my_task):
        # check errors
        form = response.context.get('form')
        self.assertGreater(len(form.errors), 0)

        # test task
        self.assertFalse(my_task.called)

    @patch('submissions.views.ImportCRBAnimTask.delay')
    def test_crb_anim_wrong_encoding(self, my_task):
        # submit a cryoweb like dictionary
        response = self.client.post(
            self.url,
            self.get_data(ds_file="latin_type"))

        # check errors
        self.common_check(response, my_task)

    @patch('submissions.views.ImportCRBAnimTask.delay')
    def test_crb_anim_wrong_columns(self, my_task):
        # submit a cryoweb like dictionary
        response = self.client.post(
            self.url,
            self.get_data(ds_file="not_valid_crbanim"))

        # check errors
        self.common_check(response, my_task)

    @patch('xlrd.book.Book.sheet_names', return_value=['animal', 'sample'])
    @patch('submissions.views.ImportTemplateTask.delay')
    def test_template_issues_in_sheets(self, my_task, my_excel):
        # submit a template file
        response = self.client.post(
            self.url,
            self.get_data(ds_file=TEMPLATE_TYPE))

        # check errors
        self.common_check(response, my_task)

        self.assertTrue(my_excel.called)

    @patch.dict(
            "excel.helpers.exceltemplate.TEMPLATE_COLUMNS",
            {'breed': ["a column"]})
    @patch('submissions.views.ImportTemplateTask.delay')
    def test_template_issues_in_columns(self, my_task):
        # submit a template file
        response = self.client.post(
            self.url,
            self.get_data(ds_file=TEMPLATE_TYPE))

        # check errors
        self.common_check(response, my_task)


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
            self.get_data(ds_file=CRB_ANIM_TYPE),
            follow=True)

        # track task
        self.my_task = my_task


class TemplateReloadSubmissionViewTest(
        SuccessfulReloadMixin, TestBase):

    @patch('submissions.views.ImportTemplateTask.delay')
    def setUp(self, my_task):
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
            self.get_data(ds_file=TEMPLATE_TYPE),
            follow=True)

        # track task
        self.my_task = my_task
