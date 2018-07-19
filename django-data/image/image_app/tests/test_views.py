#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 16:11:23 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import os

from django.test import Client, TestCase
from django.urls import resolve, reverse

import cryoweb.tests

from ..forms import DataSourceForm
from ..models import DataSource, DictCountry, User
from ..views import DataSourceView, initializedb, DashBoardView, SummaryView


class Initialize(TestCase):
    """Does the common stuff when testing cases are run"""

    def setUp(self):
        # create a testuser
        User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        self.client = Client()
        self.client.login(username='test', password='test')


class SiteTestCase(Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

    def test_homepage(self):
        """Testing home"""

        response = self.client.get(reverse('index'))

        # Check that the response is 200
        self.assertEqual(response.status_code, 200)


class DashBoardViewTest(Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url for dashboard
        self.url = reverse('image_app:dashboard')

        # get a response
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
        self.assertEquals(self.response.status_code, 200)

    def test_url_resolves_view(self):
        view = resolve('/image_app/dashboard/')
        self.assertIsInstance(view.func.view_class(), DashBoardView)

    def test_contains_navigation_links(self):
        upload_url = reverse('image_app:data_upload')
        summary_url = reverse('image_app:summary')

        self.assertContains(self.response, 'href="{0}"'.format(upload_url))
        self.assertContains(self.response, 'href="{0}"'.format(summary_url))

        # TODO: test submission link

    # TODO: test submission button inactive


class SummaryViewTest(Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url for dashboard
        self.url = reverse('image_app:summary')

        # get a response
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
        self.assertEquals(self.response.status_code, 200)

    def test_url_resolves_view(self):
        view = resolve('/image_app/summary/')
        self.assertIsInstance(view.func.view_class(), SummaryView)

    # TODO: test summary after data load


class AddDataSourceTests(Initialize):
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
            'name': 'test',
            'country': self.country.id,
            'type': 0,
            'version': '0.1',
            'uploaded_file': open(ds_path),
        }
        self.client.post(url, data)
        self.assertTrue(DataSource.objects.exists())

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
        self.assertFalse(DataSource.objects.exists())

    def test_contains_form(self):
        url = reverse('image_app:data_upload')
        response = self.client.get(url)
        form = response.context.get('form')
        self.assertIsInstance(form, DataSourceForm)


class TestInitializeDB(Initialize):
    def setUp(self):
        # create test user
        super().setUp()

    def test_new_ds_view_success_status_code(self):
        url = reverse('image_app:initializedb')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)

    def test_url_resolves_view(self):
        url = reverse('image_app:initializedb')
        view = resolve(url)
        self.assertEqual(view.func, initializedb)
