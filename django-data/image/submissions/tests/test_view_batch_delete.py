#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 16:01:38 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.constants import WAITING
from common.tests.mixins import GeneralMixinTestCase, OwnerMixinTestCase

from .common import SubmissionDataMixin
from ..views import (
    DeleteAnimalsView, DeleteSamplesView, BatchDelete)


class DeleteAnimalsViewTest(
        SubmissionDataMixin, GeneralMixinTestCase, OwnerMixinTestCase,
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
        SubmissionDataMixin, GeneralMixinTestCase, OwnerMixinTestCase,
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


class BatchDeleteMixin(
        SubmissionDataMixin, GeneralMixinTestCase):

    def tearDown(self):
        self.batch_delete_patcher.stop()

        super().tearDown()

    def test_ownership(self):
        """Test a non-owner having a 404 response"""

        client = Client()
        client.login(username='test2', password='test2')

        response = client.post(
            self.url,
            self.data,
            follow=True
        )

        self.assertEqual(response.status_code, 404)

    def test_redirect(self):
        url = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertRedirects(self.response, url)

    def test_delete(self):
        """Asserting task called"""

        self.assertTrue(self.batch_delete.called)

        self.submission.refresh_from_db()

        self.assertEqual(self.submission.status, WAITING)
        self.assertEqual(
            self.submission.message,
            "waiting for batch delete to complete")

    def test_message(self):
        """Assert message"""

        # check messages (defined in common.tests.MessageMixinTestCase
        self.check_messages(
            self.response,
            "warning",
            "waiting for batch delete to complete")


class SuccessfulDeleteAnimalsViewTest(
        BatchDeleteMixin, TestCase):

    def setUp(self):
        """call base method"""

        # call base method
        super().setUp()

        # defining patcher
        self.batch_delete_patcher = patch(
            'animals.tasks.BatchDeleteAnimals.delay')
        self.batch_delete = self.batch_delete_patcher.start()

        # explict url (is not a submission:delete view)
        self.url = reverse(
            'submissions:batch_delete',
            kwargs={'pk': 1, 'type': 'Animals'})

        self.data = {'to_delete': 'ANIMAL:::ID:::132713'}

        # get a response
        self.response = self.client.post(
            self.url,
            self.data,
            follow=True
        )

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/batch_delete/Animals/')
        self.assertIsInstance(view.func.view_class(), BatchDelete)


class SuccessfulDeleteSamplesViewTest(
        BatchDeleteMixin, TestCase):

    def setUp(self):
        """call base method"""

        # call base method
        super().setUp()

        # defining patcher
        self.batch_delete_patcher = patch(
            'samples.tasks.BatchDeleteSamples.delay')
        self.batch_delete = self.batch_delete_patcher.start()

        # explict url (is not a submission:delete view)
        self.url = reverse(
            'submissions:batch_delete',
            kwargs={'pk': 1, 'type': 'Samples'})

        self.data = {'to_delete': 'Siems_0722_393449'}

        # get a response
        self.response = self.client.post(
            self.url,
            self.data,
            follow=True
        )

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/batch_delete/Samples/')
        self.assertIsInstance(view.func.view_class(), BatchDelete)
