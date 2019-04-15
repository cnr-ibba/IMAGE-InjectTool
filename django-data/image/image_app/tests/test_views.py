#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 16:11:23 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import Client, TestCase
from django.urls import resolve, reverse

from common.tests import (
    DataSourceMixinTestCase, GeneralMixinTestCase, StatusMixinTestCase,
    OwnerMixinTestCase, LoginMixinTestCase)

from ..models import Submission
from ..views import (
    DashBoardView, SummaryView, AboutView, IndexView, PrivacyView, TermsView,
    AboutUploadingView)


class Initialize(TestCase):
    """Does the common stuff when testing cases are run"""

    fixtures = [
        "image_app/user"
    ]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')


class IndexViewTest(StatusMixinTestCase, Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # test page
        self.url = reverse('index')
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/')
        self.assertIsInstance(view.func.view_class(), IndexView)


class DashBoardViewTest(GeneralMixinTestCase, Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url for dashboard
        self.url = reverse('image_app:dashboard')

        # get a response
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/image_app/dashboard/')
        self.assertIsInstance(view.func.view_class(), DashBoardView)

    def test_contains_navigation_links(self):
        create_url = reverse('submissions:create')
        summary_url = reverse('image_app:summary')

        self.assertContains(self.response, 'href="{0}"'.format(create_url))
        self.assertContains(self.response, 'href="{0}"'.format(summary_url))

        # TODO: test resume submission link

    # TODO: test submission button inactive


class AboutViewTest(StatusMixinTestCase, Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url and a respose
        self.url = reverse('about')
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/about/')
        self.assertIsInstance(view.func.view_class(), AboutView)


class PrivacyViewTest(StatusMixinTestCase, Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url and a respose
        self.url = reverse('privacy-policy')
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/privacy/')
        self.assertIsInstance(view.func.view_class(), PrivacyView)


class TermsViewTest(StatusMixinTestCase, Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url and a respose
        self.url = reverse('terms-and-conditions')
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/terms/')
        self.assertIsInstance(view.func.view_class(), TermsView)


class AboutUploadingViewTest(StatusMixinTestCase, Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url and a respose
        self.url = reverse('about-uploading')
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/about_uploading/')
        self.assertIsInstance(view.func.view_class(), AboutUploadingView)


class SummaryViewTest(GeneralMixinTestCase, Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url for dashboard
        self.url = reverse('image_app:summary')

        # get a response
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/image_app/summary/')
        self.assertIsInstance(view.func.view_class(), SummaryView)

    # TODO: test summary after data load


class ProtectedViewTest(DataSourceMixinTestCase, OwnerMixinTestCase,
                        LoginMixinTestCase, TestCase):
    """A class to test protected view"""

    # define attribute in DataSourceMixinTestCase
    model = Submission

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission"
    ]

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.client.login(username='test', password='test')

        self.submission_id = 1
        self.submission = Submission.objects.get(pk=self.submission_id)

        self.file_name = self.submission.get_uploaded_file_basename()

        # define url
        self.url = "/protected/%s" % (self.submission.uploaded_file)

    def test_response(self):
        # get a response
        response = self.client.get(self.url)

        self.assertEqual(
            response.get('Content-Disposition'),
            'attachment; filename="{}"'.format(
                self.file_name)
        )
