#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 16:01:38 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase
from django.urls import resolve, reverse

from common.tests.mixins import (
    GeneralMixinTestCase, OwnerMixinTestCase)

from .common import SubmissionDeleteMixin
from ..views import (
    DeleteAnimalsView, DeleteSamplesView, BatchDelete)


class DeleteAnimalsViewTest(
        SubmissionDeleteMixin, GeneralMixinTestCase, OwnerMixinTestCase,
        TestCase):

    def setUp(self):
        # call base method
        super().setUp()

        # explict url (is not a submission:delete view)
        self.url = reverse('submissions:delete_animals', kwargs={'pk': 1})

        # get response (no post request)
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/delete_animals/')
        self.assertIsInstance(view.func.view_class(), DeleteAnimalsView)

    def test_not_found_status_code(self):
        url = reverse('submissions:delete_animals', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_navigation_links(self):
        """Testing link to submission detail"""

        link = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertContains(self.response, 'href="{0}"'.format(link))


class DeleteSamplesViewTest(
        SubmissionDeleteMixin, GeneralMixinTestCase, OwnerMixinTestCase,
        TestCase):

    def setUp(self):
        # call base method
        super().setUp()

        # explict url (is not a submission:delete view)
        self.url = reverse('submissions:delete_samples', kwargs={'pk': 1})

        # get response (no post request)
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/delete_samples/')
        self.assertIsInstance(view.func.view_class(), DeleteSamplesView)

    def test_not_found_status_code(self):
        url = reverse('submissions:delete_samples', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_navigation_links(self):
        """Testing link to submission detail"""

        link = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertContains(self.response, 'href="{0}"'.format(link))
