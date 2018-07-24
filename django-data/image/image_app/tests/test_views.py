#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 16:11:23 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import Client, TestCase
from django.urls import resolve, reverse

from ..models import User
from ..views import initializedb, DashBoardView, SummaryView


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
        create_url = reverse('submissions:create')
        summary_url = reverse('image_app:summary')

        self.assertContains(self.response, 'href="{0}"'.format(create_url))
        self.assertContains(self.response, 'href="{0}"'.format(summary_url))

        # TODO: test resume submission link

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
