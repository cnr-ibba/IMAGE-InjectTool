#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 16:58:41 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import resolve, reverse

from common.constants import (
    CRYOWEB_TYPE, CRB_ANIM_TYPE, TEMPLATE_TYPE, WAITING)
from image_app.models import DictCountry, Organization, Submission
from common.tests import FormMixinTestCase, InvalidFormMixinTestCase

from .common import SubmissionFormMixin
from ..forms import SubmissionForm
from ..views import CreateSubmissionView


class Initialize(SubmissionFormMixin, TestCase):
    """Does the common stuff when testing cases are run"""

    fixtures = [
        "image_app/user",
        "image_app/dictrole",
        "image_app/dictcountry",
        "image_app/organization",
    ]

    def setUp(self):
        # login as a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('submissions:create')
        self.response = self.client.get(self.url)

    def tearDown(self):
        if hasattr(self, "submission"):
            # delete uploaded file if exists
            fullpath = self.submission.uploaded_file.path

            if os.path.exists(fullpath):
                os.remove(fullpath)

        # call super method
        super().tearDown()

    def get_data(self, ds_file=CRYOWEB_TYPE):
        """Get data dictionary"""

        ds_type, ds_path = super().get_data(ds_file)

        # get required objects object
        self.country = DictCountry.objects.get(pk=1)
        self.organization = Organization.objects.get(pk=1)

        # define test data
        data = {
            'title': "Submission",
            'description': "Test Submission",
            'gene_bank_name': 'test',
            'gene_bank_country': self.country.id,
            'organization': self.organization.id,
            'datasource_type': ds_type,
            'datasource_version': '0.1',
            'uploaded_file': open(ds_path, "rb"),
        }

        return data


class CreateSubmissionViewTest(FormMixinTestCase, Initialize):
    form_class = SubmissionForm

    def test_url_resolves_view(self):
        view = resolve('/submissions/create/')
        self.assertIsInstance(view.func.view_class(), CreateSubmissionView)

    def test_form_inputs(self):

        # total input is n of form fields + (CSRF) + file
        self.assertContains(self.response, '<input', 6)
        self.assertContains(self.response, 'type="text"', 4)
        self.assertContains(self.response, 'type="file"', 1)
        self.assertContains(self.response, '<select', 3)


class SuccessfulCreateSubmissionViewTest(Initialize):
    # patch to simulate data load
    @patch('cryoweb.tasks.import_from_cryoweb.delay')
    def setUp(self, my_task):
        # create a test user
        super().setUp()

        # submit a cryoweb like dictionary
        self.response = self.client.post(
            self.url,
            self.get_data(ds_file=CRYOWEB_TYPE),
            follow=True)

        # get the submission object
        self.submission = self.response.context['submission']

        # track mocked object
        self.my_task = my_task

    def tearDown(self):
        """Override Initialize.tearDown to erase all submission objects"""

        # delete uploaded file if exists
        for submission in Submission.objects.all():
            fullpath = submission.uploaded_file.path

            if os.path.exists(fullpath):
                os.remove(fullpath)

        # call super method
        super().tearDown()

    def test_new_submission_obj(self):
        self.submission.refresh_from_db()
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(self.submission.status, WAITING)

    def test_redirect(self):
        url = reverse('submissions:detail', kwargs={'pk': self.submission.pk})
        self.assertRedirects(self.response, url)

    def test_task_called(self):
        self.assertTrue(self.my_task.called)
        self.my_task.assert_called_with(self.submission.pk)

    @patch('cryoweb.tasks.import_from_cryoweb.delay')
    def test_different_user(self, my_task):
        """Create a new submission with the same data for a different user"""

        # login as a different user
        client = Client()
        client.login(username='test2', password='test2')

        response = client.post(
            self.url,
            self.get_data(),
            follow=True)

        # get this new submission object
        self.assertEqual(Submission.objects.count(), 2)
        submission = Submission.objects.filter(owner__username="test2").first()

        # assert redirects
        url = reverse('submissions:detail', kwargs={'pk': submission.pk})
        self.assertRedirects(response, url)

        # test called task
        self.assertTrue(my_task.called)


class InvalidCreateSubmissionViewTest(InvalidFormMixinTestCase, Initialize):

    def setUp(self):
        # create a test user
        super().setUp()

        # submit an empty dictionary
        self.response = self.client.post(self.url, {})

    def test_no_new_obj(self):
        self.assertFalse(Submission.objects.exists())


class SupportedCreateSubmissionViewTest(Initialize):
    # patch to simulate data load
    @patch('submissions.views.ImportCRBAnimTask.delay')
    def test_crb_anim_loading(self, my_task):
        # submit a cryoweb like dictionary
        response = self.client.post(
            self.url,
            self.get_data(ds_file=CRB_ANIM_TYPE),
            follow=True)

        # get the submission object
        self.assertEqual(Submission.objects.count(), 1)
        self.submission = Submission.objects.first()

        # test redirect
        url = reverse('submissions:detail', kwargs={'pk': self.submission.pk})
        self.assertRedirects(response, url)

        # test status
        self.assertEqual(self.submission.status, WAITING)

        # test message
        message = "waiting for data loading"
        self.assertEqual(self.submission.message, message)

        # test task
        self.assertTrue(my_task.called)

    @patch('submissions.views.ImportTemplateTask.delay')
    def test_template_loading(self, my_task):
        # submit a cryoweb like dictionary
        response = self.client.post(
            self.url,
            self.get_data(ds_file=TEMPLATE_TYPE),
            follow=True)

        # get the submission object
        self.assertEqual(Submission.objects.count(), 1)
        self.submission = Submission.objects.first()

        # test redirect
        url = reverse('submissions:detail', kwargs={'pk': self.submission.pk})
        self.assertRedirects(response, url)

        # test status
        self.assertEqual(self.submission.status, WAITING)

        # test message
        message = "waiting for data loading"
        self.assertEqual(self.submission.message, message)

        # test task
        self.assertTrue(my_task.called)

    @patch('submissions.views.ImportCRBAnimTask.delay')
    def test_crb_anim_wrong_encoding(self, my_task):
        # submit a cryoweb like dictionary
        response = self.client.post(
            self.url,
            self.get_data(ds_file="latin_type"))

        # check errors
        form = response.context.get('form')
        self.assertGreater(len(form.errors), 0)

        # no submissions
        self.assertFalse(Submission.objects.exists())

        # test task
        self.assertFalse(my_task.called)

    @patch('submissions.views.ImportCRBAnimTask.delay')
    def test_crb_anim_wrong_columns(self, my_task):
        # submit a cryoweb like dictionary
        response = self.client.post(
            self.url,
            self.get_data(ds_file="not_valid_crbanim"))

        # check errors
        form = response.context.get('form')
        self.assertGreater(len(form.errors), 0)

        # no submissions
        self.assertFalse(Submission.objects.exists())

        # test task
        self.assertFalse(my_task.called)
