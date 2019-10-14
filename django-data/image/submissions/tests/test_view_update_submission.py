#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 12:56:11 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase
from django.urls import resolve, reverse

from common.tests import (
    FormMixinTestCase, OwnerMixinTestCase, InvalidFormMixinTestCase)

from ..forms import UpdateSubmissionForm
from ..views import UpdateSubmissionView

from .common import SubmissionDataMixin


class UpdateSubmissionViewTest(
        FormMixinTestCase, OwnerMixinTestCase, SubmissionDataMixin, TestCase):

    form_class = UpdateSubmissionForm

    def setUp(self):
        # call base method
        super().setUp()

        self.url = reverse('submissions:update', kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/update/')
        self.assertIsInstance(view.func.view_class(), UpdateSubmissionView)

    def test_form_inputs(self):
        self.assertContains(self.response, '<input', 4)
        self.assertContains(self.response, '<select', 2)

    def test_reload_not_found_status_code(self):
        url = reverse('submissions:update', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_contains_navigation_links(self):
        """Contain links to DetailSubmissionView"""

        link = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertContains(self.response, 'href="{0}"'.format(link))


class SuccessfulUpdateSubmissionViewTest(SubmissionDataMixin, TestCase):
    def setUp(self):
        # call base method
        super().setUp()

        self.data = {
            'title': 'test-edited',
            'description': 'edited-submission',
            'gene_bank_name': 'Cryoweb',
            'gene_bank_country': 1,
            'organization': 1
            }

        self.url = reverse('submissions:update', kwargs={'pk': 1})
        self.response = self.client.post(self.url, self.data, follow=True)

    def test_redirect(self):
        url = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertRedirects(self.response, url)

    def test_model_updated(self):
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.title, self.data["title"])
        self.assertEqual(self.submission.description, self.data["description"])


class InvalidUpdateSubmissionViewTest(
        InvalidFormMixinTestCase, SubmissionDataMixin, TestCase):
    def setUp(self):
        # call base method
        super().setUp()

        self.url = reverse('submissions:update', kwargs={'pk': 1})
        self.response = self.client.post(self.url, {})
