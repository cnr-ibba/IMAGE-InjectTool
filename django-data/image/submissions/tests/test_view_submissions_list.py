#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 30 13:51:17 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.urls import resolve, reverse
from django.test import Client, TestCase

from common.tests import GeneralMixinTestCase

from ..views import ListSubmissionsView


class ListSubmissionViewTest(
        GeneralMixinTestCase, TestCase):

    """Test Submission ListView"""

    fixtures = [
        "uid/user",
        "uid/dictcountry",
        "uid/dictrole",
        "uid/organization",
        "uid/submission"
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('submissions:list')
        self.response = self.client.get(self.url)

    def test_content(self):
        """Assert submission in list"""

        # get animal queryset
        qs = self.response.context['submission_list']

        # assert one animal for this user
        self.assertEqual(qs.count(), 1)

        # test submission in context data
        submission = qs.first()
        self.assertEqual(submission.description, "image test data")

    def test_ownership(self):
        """Test a non-owner have no submission. But I can access the page"""

        client = Client()
        client.login(username='test2', password='test2')

        response = client.get(self.url)

        # I will get a submission list, but I won't see loaded data
        self.assertNotContains(response, "image test data")

        # get submission queryset
        qs = response.context['submission_list']

        # assert no animals for this user
        self.assertEqual(qs.count(), 0)

    def test_url_resolves_view(self):
        view = resolve('/submissions/list/')
        self.assertIsInstance(view.func.view_class(), ListSubmissionsView)

    def test_contains_navigation_links(self):
        create_url = reverse('submissions:create')
        dashboard_url = reverse('uid:dashboard')

        self.assertContains(self.response, 'href="{0}"'.format(create_url))
        self.assertContains(self.response, 'href="{0}"'.format(dashboard_url))
