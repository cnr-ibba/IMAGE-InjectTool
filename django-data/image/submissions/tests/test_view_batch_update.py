#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 12:07:40 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import resolve, reverse

from common.constants import WAITING
from common.tests import GeneralMixinTestCase, OwnerMixinTestCase
from validation.models import ValidationSummary

from .common import SubmissionDataMixin, SubmissionStatusMixin
from ..views import SubmissionValidationSummaryFixErrorsView, FixValidation


class SubmissionValidationSummaryFixErrorsViewTest(
        SubmissionDataMixin, GeneralMixinTestCase, OwnerMixinTestCase,
        TestCase):
    """Test SubmissionValidationSummaryViewTest View"""

    def setUp(self):
        super().setUp()

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


class SubmissionValidationSummaryFixErrorsViewColumnTest(
        SubmissionDataMixin, TestCase):

    def setUp(self):
        # calling minxin methods
        super().setUp()

        self.url_animal = reverse(
            'submissions:validation_summary_fix_errors',
            kwargs={
                'pk': 1,
                'type': 'animal',
                'message_counter': 0})

        self.url_sample = reverse(
            'submissions:validation_summary_fix_errors',
            kwargs={
                'pk': 1,
                'type': 'sample',
                'message_counter': 0})

    def test_animal_age_issue(self):
        """Testing animal age column"""

        # is an animal VS
        vs = ValidationSummary.objects.get(pk=2)
        vs.messages = [{
            'message': ('Error: One of minutes, ... need to be present for the'
                        ' field Animal age at collection (specimen from '
                        'organism section'),
            'count': 1,
            'ids': [1],
            'offending_column': 'Animal age at collection'}]
        vs.save()

        # get animal page
        response = self.client.get(self.url_sample)
        self.assertEqual(response.status_code, 200)

    def test_accuracy_issue(self):
        """Testing animal age column"""

        # is an animal VS
        vs = ValidationSummary.objects.get(pk=1)
        vs.messages = [{
            'message': ('Error: .* of field .* is not in the valid values '
                        'list .*'),
            'count': 1,
            'ids': [1],
            'offending_column': 'Birth location accuracy'}]
        vs.save()

        # get animal page
        response = self.client.get(self.url_animal)
        self.assertEqual(response.status_code, 200)

    def test_storage_processing_issue(self):
        """Testing sample storage processing column"""

        # is an animal VS
        vs = ValidationSummary.objects.get(pk=2)
        vs.messages = [{
            'message': ('Error: .* of field .* is not in the valid values '
                        'list .*'),
            'count': 1,
            'ids': [1],
            'offending_column': 'Sample storage processing'}]
        vs.save()

        # get animal page
        response = self.client.get(self.url_sample)
        self.assertEqual(response.status_code, 200)

    def test_storage_issue(self):
        """Testing sample storage processing column"""

        # is an animal VS
        vs = ValidationSummary.objects.get(pk=2)
        vs.messages = [{
            'message': ('Error: .* of field .* is not in the valid values '
                        'list .*'),
            'count': 1,
            'ids': [1],
            'offending_column': 'Sample storage'}]
        vs.save()

        # get animal page
        response = self.client.get(self.url_sample)
        self.assertEqual(response.status_code, 200)


class NoBatchUpdateTest(
        SubmissionDataMixin, SubmissionStatusMixin, TestCase):
    """Test if I can batch delete relying on status"""

    def setUp(self):
        # call base method
        super().setUp()

        # explict url (is not a submission:delete view)
        self.url = reverse(
            'submissions:validation_summary_fix_errors',
            kwargs={
                'pk': 1,
                'type': 'animal',
                'message_counter': 0})
        self.redirect_url = reverse('submissions:detail', kwargs={'pk': 1})


class FixValidationMixin(
        SubmissionDataMixin, GeneralMixinTestCase):

    def tearDown(self):
        self.batch_update_patcher.stop()

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

    def test_update(self):
        """Asserting task called"""

        self.assertTrue(self.batch_update.called)

        self.submission.refresh_from_db()

        self.assertEqual(self.submission.status, WAITING)
        self.assertEqual(
            self.submission.message,
            "waiting for data updating")

    def test_message(self):
        """Assert message"""

        # check messages (defined in common.tests.MessageMixinTestCase
        self.check_messages(
            self.response,
            "warning",
            "waiting for data updating")


class SuccessfulFixValidationAnimalTest(
        FixValidationMixin, TestCase):

    def setUp(self):
        """call base method"""

        # call base method
        super().setUp()

        # defining patcher
        self.batch_update_patcher = patch(
            'animals.tasks.BatchUpdateAnimals.delay')
        self.batch_update = self.batch_update_patcher.start()

        # setting attribute
        self.attribute_to_edit = 'birth_location'

        self.url = reverse(
            'submissions:fix_validation',
            kwargs={
                'pk': 1,
                'record_type': 'animal',
                'attribute_to_edit': self.attribute_to_edit})

        self.data = {'to_edit1': 'Meow'}

        # get a response
        self.response = self.client.post(
            self.url,
            self.data,
            follow=True
        )

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/fix_validation/animal/birth_location/')
        self.assertIsInstance(view.func.view_class(), FixValidation)

    def test_called_args(self):
        """Testing used arguments"""
        self.batch_update.assert_called_with(
            str(self.submission.id),
            {1: "Meow"},
            self.attribute_to_edit)


class SuccessfulFixValidationSampleTest(
        FixValidationMixin, TestCase):

    def setUp(self):
        """call base method"""

        # call base method
        super().setUp()

        # defining patcher
        self.batch_update_patcher = patch(
            'samples.tasks.BatchUpdateSamples.delay')
        self.batch_update = self.batch_update_patcher.start()

        # setting attribute
        self.attribute_to_edit = 'collection_place'

        self.url = reverse(
            'submissions:fix_validation',
            kwargs={
                'pk': 1,
                'record_type': 'sample',
                'attribute_to_edit': self.attribute_to_edit})

        self.data = {'to_edit1': 'Meow'}

        # get a response
        self.response = self.client.post(
            self.url,
            self.data,
            follow=True
        )

    def test_url_resolves_view(self):
        view = resolve(
            '/submissions/1/fix_validation/sample/collection_place/')
        self.assertIsInstance(view.func.view_class(), FixValidation)

    def test_called_args(self):
        """Testing used arguments"""
        self.batch_update.assert_called_with(
            str(self.submission.id),
            {1: "Meow"},
            self.attribute_to_edit)
