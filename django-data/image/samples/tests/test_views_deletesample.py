#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 16:00:29 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse

from uid.models import Animal, Sample, Name
from validation.models import ValidationResult
from common.tests import MessageMixinTestCase

from .common import (
    SampleFeaturesMixin, SampleViewTestMixin, SampleStatusMixin, READY)
from ..views import DeleteSampleView


class DeleteSampleViewTest(
        SampleViewTestMixin, TestCase):

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

        self.url = reverse("samples:delete", kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/samples/1/delete/')
        self.assertIsInstance(view.func.view_class(), DeleteSampleView)

    def test_reload_not_found_status_code(self):
        url = reverse('samples:delete', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_navigation_links(self):
        """Testing link to a javascript function"""

        link = "javascript:{goBack()}"
        self.assertContains(self.response, 'href="{0}"'.format(link))


class DeleteSampleViewStatusesTest(
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
        self.url = reverse("samples:delete", kwargs={'pk': 1})
        self.redirect_url = self.sample.get_absolute_url()


# Here, I'm already tested the urls, csfr. So BaseTest
class SuccessfulDeleteSampleViewTest(
        SampleFeaturesMixin, MessageMixinTestCase, TestCase):

    def setUp(self):
        """call base method"""

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        # get objects
        sample = Sample.objects.get(pk=1)
        self.submission = sample.submission

        # count number of animals and names
        self.n_of_animals = Animal.objects.count()
        self.n_of_names = Name.objects.count()

        # update submission status (to get this url)
        self.submission.status = READY
        self.submission.save()

        # set validation result (since is not present in features)
        validation = ValidationResult()
        validation.status = "Pass"
        sample.name.validationresult = validation
        sample.name.save()

        self.url = reverse("samples:delete", kwargs={'pk': 1})
        self.response = self.client.post(
            self.url,
            {},
            follow=True
        )

    def test_redirect(self):
        url = reverse('submissions:edit', kwargs={'pk': self.submission.pk})
        self.assertRedirects(self.response, url)

    def test_sample_delete(self):
        """Deleting a sample will delete its name and validationresult"""

        # Animals objects are the same
        n_animals = Animal.objects.count()
        self.assertEqual(n_animals, self.n_of_animals)

        # no samples
        n_samples = Sample.objects.count()
        self.assertEqual(n_samples, 0)

        # 1 names was deleted
        n_names = Name.objects.count()
        self.assertEqual(n_names, self.n_of_names-1)

        # check for ramaining names
        names = [name.name for name in Name.objects.all()]
        self.assertIn("ANIMAL:::ID:::unknown_sire", names)
        self.assertIn("ANIMAL:::ID:::unknown_dam", names)
        self.assertIn("ANIMAL:::ID:::132713", names)
        self.assertIn("ANIMAL:::ID:::mother", names)
        self.assertIn("ANIMAL:::ID:::son", names)

        # check for validationresults
        n_validation = ValidationResult.objects.count()
        self.assertEqual(n_validation, 1)

    def test_statuses(self):
        # reload submission
        self.submission.refresh_from_db()

        # test status for submission (doesn't change for delete)
        self.assertEqual(self.submission.status, READY)

    def test_message(self):
        """Assert 'successfully deleted' message"""

        # check messages (defined in common.tests.MessageMixinTestCase
        self.check_messages(
            self.response,
            "info",
            "was successfully deleted")
