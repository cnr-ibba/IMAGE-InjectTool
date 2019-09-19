#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 12:07:40 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import Client, TestCase
from django.urls import resolve, reverse

from common.tests import GeneralMixinTestCase, OwnerMixinTestCase
from validation.models import ValidationSummary

from ..views import SubmissionValidationSummaryFixErrorsView


class SubmissionValidationSummaryFixErrorsViewTest(
        GeneralMixinTestCase, OwnerMixinTestCase, TestCase):
    """Test SubmissionValidationSummaryViewTest View"""

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission",
        "validation/validationsummary"
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse(
            'submissions:validation_summary_fix_errors',
            kwargs={
                'pk': 1,
                'type': 'animal',
                'message_counter': 0})

        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/validation_summary/animal/0/')
        self.assertIsInstance(
            view.func.view_class(),
            SubmissionValidationSummaryFixErrorsView)

    def test_view_not_found_status_code(self):
        url = reverse(
            'submissions:validation_summary_fix_errors',
            kwargs={
                'pk': 99,
                'type': 'animal',
                'message_counter': 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
