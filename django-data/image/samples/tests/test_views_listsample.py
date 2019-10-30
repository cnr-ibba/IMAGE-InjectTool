#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 15:40:00 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse

from .common import SampleViewTestMixin
from ..views import ListSampleView


class ListSampleViewTest(SampleViewTestMixin, TestCase):
    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('samples:list')
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/samples/list/')
        self.assertIsInstance(view.func.view_class(), ListSampleView)

    def test_ownership(self):
        """Ovverride default test_ownership"""

        client = Client()
        client.login(username='test2', password='test2')

        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # get sample queryset
        qs = response.context['sample_list']

        # assert no samples for this user
        self.assertEqual(qs.count(), 0)

    def test_content(self):
        """Assert submission in list"""

        # get sample queryset
        qs = self.response.context['sample_list']

        # assert one sample for this user
        self.assertEqual(qs.count(), 1)

        names = [sample.name.name for sample in qs.all()]
        self.assertIn("Siems_0722_393449", names)

    def test_contains_navigation_links(self):
        submission_url = reverse('submissions:list')
        dashboard_url = reverse('uid:dashboard')

        self.assertContains(self.response, 'href="{0}"'.format(submission_url))
        self.assertContains(self.response, 'href="{0}"'.format(dashboard_url))
