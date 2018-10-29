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

import cryoweb.tests
from image_app.models import DictCountry, Organization, Submission, STATUSES

from ..forms import SubmissionForm
from ..views import CreateSubmissionView


# get template types from submission object
CRYOWEB_TYPE = Submission.TYPES.get_value('cryoweb')
TEMPLATE_TYPE = Submission.TYPES.get_value('template')
CRB_ANIM_TYPE = Submission.TYPES.get_value('crb_anim')

# get submission status
ERROR = STATUSES.get_value('error')


class Initialize(TestCase):
    """Does the common stuff when testing cases are run"""

    fixtures = [
        "submissions/user",
        "image_app/dictrole",
        "submissions/dictcountry",
        "submissions/organization",
    ]

    def setUp(self):
        # login as a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('submissions:create')
        self.response = self.client.get(self.url)

    def get_data(self, ds_type=CRYOWEB_TYPE):
        """Get data dictionary"""

        # get data source path
        ds_path = os.path.join(
            cryoweb.tests.__path__[0],
            "cryoweb_test_data_only.sql"
        )

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
            'uploaded_file': open(ds_path),
        }

        return data


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
        self.assertEqual(self.response.status_code, 200)

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
            self.get_data(),
            follow=True)

        # get the submission object
        self.submission = Submission.objects.first()

        # track mocked object
        self.my_task = my_task

    def tearDown(self):
        # delete uploaded file if exists
        fullpath = self.submission.uploaded_file.path

        if os.path.exists(fullpath):
            os.remove(fullpath)

        # call super method
        super().tearDown()

    def test_new_submission_obj(self):
        self.assertTrue(Submission.objects.exists())

    def test_redirect(self):
        url = reverse('submissions:detail', kwargs={'pk': self.submission.pk})
        self.assertRedirects(self.response, url)

    def test_new_not_found_status_code(self):
        url = reverse('submissions:detail', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_task_called(self):
        self.my_task.assert_called_with(self.submission.pk)


class InvalidCreateSubmissionViewTest(Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # submit an empty dictionary
        self.response = self.client.post(self.url, {})

    def test_status_code(self):
        '''
        An invalid form submission should return to the same page
        '''

        self.assertEqual(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertGreater(len(form.errors), 0)

    def test_no_new_obj(self):
        self.assertFalse(Submission.objects.exists())


class UnsupportedCreateSubmissionViewTest(Initialize):
    def tearDown(self):
        # delete uploaded file if exists
        fullpath = self.submission.uploaded_file.path

        if os.path.exists(fullpath):
            os.remove(fullpath)

        # call super method
        super().tearDown()

    def test_template_loading(self):
        # submit a cryoweb like dictionary
        response = self.client.post(
            self.url,
            self.get_data(ds_type=TEMPLATE_TYPE),
            follow=True)

        # get the submission object
        self.submission = Submission.objects.first()

        # test redirect
        url = reverse('submissions:detail', kwargs={'pk': self.submission.pk})
        self.assertRedirects(response, url)

        # test status
        self.assertEqual(self.submission.status, ERROR)

        # test message
        message = "Template import is not implemented"
        self.assertEqual(self.submission.message, message)

    def test_crb_anim_loading(self):
        # submit a cryoweb like dictionary
        response = self.client.post(
            self.url,
            self.get_data(ds_type=CRB_ANIM_TYPE),
            follow=True)

        # get the submission object
        self.submission = Submission.objects.first()

        # test redirect
        url = reverse('submissions:detail', kwargs={'pk': self.submission.pk})
        self.assertRedirects(response, url)

        # test status
        self.assertEqual(self.submission.status, ERROR)

        # test message
        message = "CRB-Anim import is not implemented"
        self.assertEqual(self.submission.message, message)
