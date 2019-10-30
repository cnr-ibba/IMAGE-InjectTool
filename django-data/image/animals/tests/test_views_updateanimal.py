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
from uid.models import Animal, Submission, ACCURACIES

from ..views import UpdateAnimalView
from ..forms import UpdateAnimalForm
from .common import (
    AnimalFeaturesMixin, AnimalViewTestMixin, AnimalStatusMixin, READY,
    NEED_REVISION, LOADED)

# get accuracy levels
PRECISE = ACCURACIES.get_value('precise')
MISSING = ACCURACIES.get_value('missing')

# get a timestamp
NOW = timezone.now()


class UpdateAnimalViewTest(
        FormMixinTestCase, AnimalViewTestMixin, TestCase):

    # required by FormMixinTestCase
    form_class = UpdateAnimalForm

    def setUp(self):
        """call base method"""

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        # get objects
        self.animal = Animal.objects.get(pk=1)
        self.submission = self.animal.submission

        # update submission status (to get this url)
        self.submission.status = READY
        self.submission.save()

        self.url = reverse("animals:update", kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/animals/1/update/')
        self.assertIsInstance(view.func.view_class(), UpdateAnimalView)

    def test_reload_not_found_status_code(self):
        url = reverse('animals:update', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_form_inputs(self):
        # csrfmiddlewaretoken is tested by FormMixinTestCase
        self.assertContains(self.response, '<div class="form-group">', 12)
        self.assertContains(self.response, '<input type="text"', 7)
        self.assertContains(self.response, '<input type="number"', 2)
        self.assertContains(self.response, '<select ', 3)
        self.assertContains(
            self.response, '<select name="breed"', 1)
        self.assertContains(
            self.response, '<select name="sex"', 1)
        self.assertContains(
            self.response, '<select name="birth_location_accuracy"', 1)

    def test_contains_navigation_links(self):
        """Testing link to a javascript function"""

        link = "javascript:{goBack()}"
        self.assertContains(self.response, 'href="{0}"'.format(link))


class UpdateAnimalViewStatusesTest(
        AnimalFeaturesMixin, AnimalStatusMixin, TestCase):
    """Test page access with different submission status"""

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        # get objects
        self.animal = Animal.objects.get(pk=1)
        self.submission = self.animal.submission

        # set URLS
        self.url = reverse("animals:update", kwargs={'pk': 1})
        self.redirect_url = self.animal.get_absolute_url()


# Here, I'm already tested the urls, csfr. So BaseTest
class SuccessfulUpdateAnimalViewTest(
        AnimalFeaturesMixin, MessageMixinTestCase, TestCase):

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

        self.url = reverse("animals:update", kwargs={'pk': 1})
        self.response = self.client.post(
            self.url,
            {'alternative_id': 11,
             'description': self.description,
             "breed": 1,
             "sex": 1,
             'birth_location': self.location,
             'birth_location_latitude': self.latitude,
             'birth_location_longitude': self.longitude,
             'birth_location_accuracy': PRECISE},
            follow=True
        )

    def test_redirect(self):
        url = reverse("animals:detail", kwargs={'pk': 1})
        self.assertRedirects(self.response, url)

    def test_animal_updated(self):
        # get an animal object
        animal = Animal.objects.get(pk=1)

        self.assertEqual(animal.description, self.description)
        self.assertEqual(animal.birth_location, self.location)
        self.assertEqual(animal.birth_location_latitude, self.latitude)
        self.assertEqual(animal.birth_location_longitude, self.longitude)
        self.assertEqual(animal.birth_location_accuracy, PRECISE)

    def test_statuses(self):
        # reload submission
        self.submission.refresh_from_db()

        # test status for submission
        self.assertEqual(self.submission.status, NEED_REVISION)
        self.assertIn("Data has changed", self.submission.message)

        # get an animal object
        animal = Animal.objects.get(pk=1)

        # test status for animal
        self.assertEqual(animal.name.status, NEED_REVISION)
        self.assertEqual(animal.name.validationresult.status, 'Info')
        self.assertListEqual(
            animal.name.validationresult.messages,
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
        # get an animal object
        animal = Animal.objects.get(pk=1)

        # assert my method was called
        self.assertTrue(self.mytime.called)

        # assert time was updated
        self.assertEqual(animal.name.last_changed, NOW)


class InvalidUpdateAnimalViewTest(
        AnimalFeaturesMixin, TestCase):

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

        # get update url
        self.url = reverse("animals:update", kwargs={'pk': 1})

    def check_form_errors(self, response):
        # check status
        self.assertEqual(response.status_code, 200)

        form = response.context.get('form')
        self.assertGreater(len(form.errors), 0)

    def check_no_update(self):
        # get an animal object
        animal = Animal.objects.get(pk=1)

        self.assertEqual(animal.description, "a 4-year old pig organic fed")
        self.assertEqual(animal.birth_location, None)
        self.assertEqual(animal.birth_location_latitude, None)
        self.assertEqual(animal.birth_location_longitude, None)
        self.assertEqual(animal.birth_location_accuracy, MISSING)

    def check_statuses(self):
        # reload submission
        self.submission.refresh_from_db()

        # test status for submission
        self.assertEqual(self.submission.status, READY)

        # get an animal object
        animal = Animal.objects.get(pk=1)

        # test status for animal (default one)
        self.assertEqual(animal.name.status, LOADED)

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
            {'description': description,
             'birth_location': location,
             'birth_location_latitude': latitude,
             'birth_location_longitude': longitude,
             'birth_location_accuracy': PRECISE},
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
            {'birth_location': location,
             'birth_location_accuracy': MISSING},
            follow=True)

        self.check_form_errors(response)
        self.check_no_update()
        self.check_statuses()
