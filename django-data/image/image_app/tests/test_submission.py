#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 11:08:12 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os

from django.urls import resolve, reverse

from ..forms import DataSourceForm
from ..models import Submission, DictCountry
from ..views import DataSourceView

from .test_views import Initialize
import cryoweb.tests


class SubmissionViewTest(Initialize):
    def setUp(self):
        # create test user
        super().setUp()

        # and now create a country object
        self.country = DictCountry.objects.create(
            label='Germany',
            term='NCIT_C16636')

    def test_new_ds_view_success_status_code(self):
        url = reverse('image_app:data_upload')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_new_ds_url_resolves_new_ds_view(self):
        url = reverse('image_app:data_upload')
        view = resolve(url)
        self.assertIsInstance(view.func.view_class(), DataSourceView)

    def test_new_ds_view_contains_link_back_to_dashboard_view(self):
        new_ds_url = reverse('image_app:data_upload')
        dashboard_url = reverse('image_app:dashboard')
        response = self.client.get(new_ds_url)
        self.assertContains(response, 'href="{0}"'.format(dashboard_url))

    def test_csrf(self):
        url = reverse('image_app:data_upload')
        response = self.client.get(url)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_new_ds_valid_post_data(self):
        # get data source path
        ds_path = os.path.join(
            cryoweb.tests.__path__[0],
            "cryoweb_test_data_only.sql"
        )
        url = reverse('image_app:data_upload')
        data = {
            'gene_bank_name': 'test',
            'gene_bank_country': self.country.id,
            'datasource_type': 0,
            'datasource_version': '0.1',
            'uploaded_file': open(ds_path),
        }
        self.client.post(url, data)
        self.assertTrue(Submission.objects.exists())

    def test_new_ds_invalid_post_data(self):
        '''
        Invalid post data should not redirect
        The expected behavior is to show the form again with validation errors
        '''
        url = reverse('image_app:data_upload')
        response = self.client.post(url, {})
        form = response.context.get('form')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(form.errors)

    def test_new_topic_invalid_post_data_empty_fields(self):
        '''
        Invalid post data should not redirect
        The expected behavior is to show the form again with validation errors
        '''

        url = reverse('image_app:data_upload')
        data = {
            'name': '',
            'country': '',
            'type': '',
            'version': '',
            'uploaded_file': '',
        }

        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)
        self.assertFalse(Submission.objects.exists())

    def test_contains_form(self):
        url = reverse('image_app:data_upload')
        response = self.client.get(url)
        form = response.context.get('form')
        self.assertIsInstance(form, DataSourceForm)
