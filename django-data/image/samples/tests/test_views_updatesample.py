#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 15:48:19 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import resolve, reverse
from django.utils import timezone

from common.tests import FormMixinTestCase, MessageMixinTestCase
from common.constants import (
    PRECISE, MISSING, UNKNOWN, READY, NEED_REVISION, LOADED)
from uid.models import Sample, Submission

from ..views import UpdateSampleView
from ..forms import UpdateSampleForm
from .common import (
    SampleFeaturesMixin, SampleViewTestMixin, SampleStatusMixin)

# get a timestamp
NOW = timezone.now()


class UpdateSampleViewTest(
        FormMixinTestCase, SampleViewTestMixin, TestCase):

    # required by FormMixinTestCase
    form_class = UpdateSampleForm

    def setUp(self):
        """call base method"""

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        # get objects
        self.sample = Sample.objects.get(pk=1)
        self.submission = self.sample.submission

        # update submission status (to get this url)
        self.submission.status = READY
        self.submission.save()

        self.url = reverse("samples:update", kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/samples/1/update/')
        self.assertIsInstance(view.func.view_class(), UpdateSampleView)

    def test_reload_not_found_status_code(self):
        url = reverse('samples:update', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_form_inputs(self):
        # csrfmiddlewaretoken is tested by FormMixinTestCase
        self.assertContains(self.response, '<div class="form-group">', 20)
        self.assertContains(self.response, '<input type="text"', 8)
        self.assertContains(self.response, '<input type="number"', 4)
        self.assertContains(self.response, '<select ', 8)
        self.assertContains(
            self.response, '<select name="collection_place_accuracy"', 1)
        self.assertContains(
            self.response, '<select name="organism_part"', 1)
        self.assertContains(
            self.response, '<select name="developmental_stage"', 1)
        self.assertContains(
            self.response, '<select name="physiological_stage"', 1)

    def test_contains_navigation_links(self):
        """Testing link to a javascript function"""

        link = "javascript:{goBack()}"
        self.assertContains(self.response, 'href="{0}"'.format(link))


class UpdateSampleViewStatusesTest(
        SampleFeaturesMixin, SampleStatusMixin, TestCase):
    """Test page access with different submission status"""

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        # get objects
        self.sample = Sample.objects.get(pk=1)
        self.submission = self.sample.submission

        # set URLS
        self.url = reverse("samples:update", kwargs={'pk': 1})
        self.redirect_url = self.sample.get_absolute_url()


# Here, I'm already tested the urls, csfr. So BaseTest
class SuccessfulUpdateSampleViewTest(
        SampleFeaturesMixin, MessageMixinTestCase, TestCase):

    # inspired from https://stackoverflow.com/a/3155865/4385116
    @patch('common.views.timezone.now', return_value=NOW)
    def setUp(self, mytime):
        """call base method"""

        # traclk my mock function
        self.mytime = mytime

        # The values I need to modify
        self.description = "A new description"
        self.location = "Milano"
        self.latitude = 45.4654219
        self.longitude = 9.1859243

        # a submission object
        self.submission = Submission.objects.get(pk=1)

        # update status
        self.submission.status = READY
        self.submission.save()

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse("samples:update", kwargs={'pk': 1})
        self.response = self.client.post(
            self.url,
            {'alternative_id': 11,
             'description': self.description,
             'collection_place': self.location,
             'collection_place_latitude': self.latitude,
             'collection_place_longitude': self.longitude,
             'collection_place_accuracy': PRECISE,
             'organism_part': 1},
            follow=True
        )

    def test_redirect(self):
        url = reverse("samples:detail", kwargs={'pk': 1})
        self.assertRedirects(self.response, url)

    def test_sample_updated(self):
        # get an sample object
        sample = Sample.objects.get(pk=1)

        self.assertEqual(sample.description, self.description)
        self.assertEqual(sample.collection_place, self.location)
        self.assertEqual(sample.collection_place_latitude, self.latitude)
        self.assertEqual(sample.collection_place_longitude, self.longitude)
        self.assertEqual(sample.collection_place_accuracy, PRECISE)

    def test_statuses(self):
        # reload submission
        self.submission.refresh_from_db()

        # test status for submission
        self.assertEqual(self.submission.status, NEED_REVISION)
        self.assertIn("Data has changed", self.submission.message)

        # get an sample object
        sample = Sample.objects.get(pk=1)

        # test status for sample
        self.assertEqual(sample.status, NEED_REVISION)
        self.assertEqual(sample.validationresult.status, 'Info')
        self.assertListEqual(
            sample.validationresult.messages,
            ['Info: Data has changed, validation has to be called']
        )

    def test_message(self):
        """Assert 'need validation' message"""

        # check messages (defined in common.tests.MessageMixinTestCase
        self.check_messages(
            self.response,
            "info",
            "Info: Data has changed, validation has to be called")

    def test_updated_time(self):
        # get an sample object
        sample = Sample.objects.get(pk=1)

        # assert my method was called
        self.assertTrue(self.mytime.called)

        # assert time was updated
        self.assertEqual(sample.last_changed, NOW)


class InvalidUpdateSampleViewTest(
        SampleFeaturesMixin, TestCase):

    def setUp(self):
        """call base method"""

        # a submission object
        self.submission = Submission.objects.get(pk=1)

        # update status
        self.submission.status = READY
        self.submission.save()

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse("samples:update", kwargs={'pk': 1})

    def check_form_errors(self, response):
        # check status
        self.assertEqual(response.status_code, 200)

        form = response.context.get('form')
        self.assertGreater(len(form.errors), 0)

    def check_no_update(self):
        # get an sample object
        sample = Sample.objects.get(pk=1)

        self.assertEqual(
            sample.description, "semen collected when the animal turns to 4")
        self.assertEqual(sample.collection_place, "deutschland")
        self.assertEqual(sample.collection_place_latitude, None)
        self.assertEqual(sample.collection_place_longitude, None)
        self.assertEqual(sample.collection_place_accuracy, UNKNOWN)

    def check_statuses(self):
        # reload submission
        self.submission.refresh_from_db()

        # test status for submission
        self.assertEqual(self.submission.status, READY)

        # get an sample object
        sample = Sample.objects.get(pk=1)

        # test status for sample (default one)
        self.assertEqual(sample.status, LOADED)

    def test_fake_coordinates(self):
        """Test form with text into numeric fields"""

        # The values I need to modify
        description = "A new description"
        location = "Milano"
        latitude = "meow"
        longitude = "bark"

        # there are no mandatory fields. Check against known validators
        # and not providing breeds and sex
        response = self.client.post(
            self.url,
            {'alternative_id': 11,
             'description': description,
             'collection_place': location,
             'collection_place_latitude': latitude,
             'collection_place_longitude': longitude,
             'collection_place_accuracy': PRECISE,
             'organism_part': 1},
            follow=True)

        self.check_form_errors(response)
        self.check_no_update()
        self.check_statuses()

    def test_no_missing_with_location(self):
        """Test missing coordinate with a location raise errors"""

        # The values I need to modify
        location = "Milano"

        # there are no mandatory fields. Check against known validators
        # and not providing breeds and sex
        response = self.client.post(
            self.url,
            {'alternative_id': 11,
             'collection_place': location,
             'collection_place_accuracy': MISSING,
             'organism_part': 1},
            follow=True)

        self.check_form_errors(response)
        self.check_no_update()
        self.check_statuses()
