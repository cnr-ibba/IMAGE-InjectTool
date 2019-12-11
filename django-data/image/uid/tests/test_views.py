#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 16:11:23 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import Client, TestCase
from django.urls import resolve, reverse

from common.tests import (
    GeneralMixinTestCase, StatusMixinTestCase, FormMixinTestCase,
    OwnerMixinTestCase, LoginMixinTestCase)

from . import DataSourceMixinTestCase, PersonMixinTestCase
from ..forms import OrganizationForm
from ..models import Submission
from ..views import (
    DashBoardView, SummaryView, AboutView, IndexView, PrivacyView, TermsView,
    AboutUploadingView, UpdateOrganizationView, AboutSubmissionView)


class Initialize(TestCase):
    """Does the common stuff when testing cases are run"""

    fixtures = [
        "uid/user"
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
        self.url = reverse('uid:dashboard')

        # get a response
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/uid/dashboard/')
        self.assertIsInstance(view.func.view_class(), DashBoardView)

    def test_contains_navigation_links(self):
        create_url = reverse('submissions:create')
        summary_url = reverse('uid:summary')

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


class AboutSubmissionViewTest(StatusMixinTestCase, Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url and a respose
        self.url = reverse('about-submission')
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/about_submission/')
        self.assertIsInstance(view.func.view_class(), AboutSubmissionView)


class SummaryViewTest(GeneralMixinTestCase, Initialize):
    def setUp(self):
        # create a test user
        super().setUp()

        # get the url for dashboard
        self.url = reverse('uid:summary')

        # get a response
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/uid/summary/')
        self.assertIsInstance(view.func.view_class(), SummaryView)

    # TODO: test summary after data load


class ProtectedViewTest(DataSourceMixinTestCase, OwnerMixinTestCase,
                        LoginMixinTestCase, TestCase):
    """A class to test protected view"""

    fixtures = [
        "uid/user",
        "uid/dictcountry",
        "uid/dictrole",
        "uid/organization",
        "uid/submission"
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


class UpdateOrganizationViewTest(
        FormMixinTestCase, PersonMixinTestCase, Initialize):
    """A class to test UpdateOrganizationView"""

    form_class = OrganizationForm

    fixtures = [
        "uid/user",
        "uid/dictcountry",
        "uid/dictrole",
        "uid/organization",
    ]

    def setUp(self):
        """call base method"""
        super().setUp()

        self.url = reverse("uid:organization_update")
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/uid/organization/update/')
        self.assertIsInstance(view.func.view_class(), UpdateOrganizationView)

    def test_form_inputs(self):

        # total input is n of form fields + (CSRF) + 1 select
        self.assertContains(self.response, '<input', 4)
        self.assertContains(self.response, 'type="text"', 2)
        self.assertContains(self.response, '<select', 2)
        self.assertContains(self.response, "required disabled", 1)

        # this is specific to my data
        self.assertContains(
            self.response,
            'name="name" value="Test organization"')

# HINT: I don't have to test succesful or invalid update cases, since
# OrganizationForm inherit from well tested modules and has no custom methods
# (apart get_object, which is implicitely tested)
