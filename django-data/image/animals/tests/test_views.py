#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 13:52:26 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import resolve, reverse
from django.utils import timezone

from common.tests import (
    GeneralMixinTestCase, OwnerMixinTestCase, FormMixinTestCase,
    InvalidFormMixinTestCase, MessageMixinTestCase)

from image_app.models import ACCURACIES, STATUSES, Animal, Submission

from ..views import DetailAnimalView, UpdateAnimalView
from ..forms import UpdateAnimalForm
from .common import AnimalFeaturesMixin

# get accuracy levels
PRECISE = ACCURACIES.get_value('precise')
MISSING = ACCURACIES.get_value('missing')

# get statuses
READY = STATUSES.get_value('ready')
NEED_REVISION = STATUSES.get_value('need_revision')
LOADED = STATUSES.get_value('loaded')

# get a timestamp
NOW = timezone.now()


class AnimalViewTestMixin(
        AnimalFeaturesMixin, GeneralMixinTestCase, OwnerMixinTestCase):
    pass


class DetailAnimalViewTest(
        AnimalViewTestMixin, TestCase):

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('animals:detail', kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/animals/1/')
        self.assertIsInstance(view.func.view_class(), DetailAnimalView)

    def test_edit_not_found_status_code(self):
        url = reverse('submissions:edit', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_contains_navigation_links(self):
        """Contain links to ListAnimalView, EditAnimalView DeleteAnimalView
        and SubmissionEditView"""

        animal_list_url = reverse('animals:list')
        submission_edit_url = reverse('submissions:edit', kwargs={'pk': 1})
        animal_update_url = reverse('animals:update', kwargs={'pk': 1})
        animal_delete_url = reverse('animals:delete', kwargs={'pk': 1})

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    animal_list_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    submission_edit_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    animal_update_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    animal_delete_url))


class DetailAnimalViewMessagesTest(
        AnimalFeaturesMixin, MessageMixinTestCase, TestCase):
    """Test messages in DetailAnimalView"""

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('animals:detail', kwargs={'pk': 1})

        # get an animal object
        animal = Animal.objects.get(pk=1)

        # get validation result
        self.validationresult = animal.name.validationresult

    def check_message(self, message_type, message_str):
        """Test messages in DetailAnimalView"""

        self.validationresult.messages = [message_str]
        self.validationresult.save()

        # get the page
        response = self.client.get(self.url)

        # check messages (defined in common.tests.MessageMixinTestCase
        self.check_messages(
            response,
            message_type,
            message_str)

    def test_info_message(self):
        """Test info message in AnimalDetailView"""

        # define a info string
        message_str = "Info: test"
        self.check_message('info', message_str)

    def test_warning_message(self):
        """Test warning message in AnimalDetailView"""

        # define a warning string
        message_str = "Warning: test"
        self.check_message('warning', message_str)

    def test_error_message(self):
        """Test error message in AnimalDetailView"""

        # define a error string
        message_str = "Error: test"
        self.check_message('error', message_str)

        # another error string
        message_str = "test"
        self.check_message('error', message_str)


class UpdateAnimalViewTest(
        FormMixinTestCase, AnimalViewTestMixin, TestCase):

    # required by FormMixinTestCase
    form_class = UpdateAnimalForm

    def setUp(self):
        """call base method"""

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

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
        self.assertContains(self.response, '<div class="form-group">', 11)
        self.assertContains(self.response, '<input type="text"', 6)
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


# Here, I'm already tested the urls, csfr. So BaseTest
class SuccessfulUpdateAnimalViewTest(
        AnimalFeaturesMixin, MessageMixinTestCase, TestCase):

    # inspired from https://stackoverflow.com/a/3155865/4385116
    @patch('animals.views.timezone.now', return_value=NOW)
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


class InvalidUpdateSpeciesViewTest(
        AnimalFeaturesMixin, InvalidFormMixinTestCase, TestCase):

    def setUp(self):
        """call base method"""

        # The values I need to modify
        self.description = "A new description"
        self.location = "Milano"
        self.latitude = "meow"
        self.longitude = "bark"

        # a submission object
        self.submission = Submission.objects.get(pk=1)

        # update status
        self.submission.status = READY
        self.submission.save()

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse("animals:update", kwargs={'pk': 1})

        # there are no mandatory fields. Check against known validators
        # and not providing breeds and sex
        self.response = self.client.post(
            self.url,
            {'description': self.description,
             'birth_location': self.location,
             'birth_location_latitude': self.latitude,
             'birth_location_longitude': self.longitude,
             'birth_location_accuracy': PRECISE},
            follow=True)

    def test_no_update(self):
        # get an animal object
        animal = Animal.objects.get(pk=1)

        self.assertEqual(animal.description, "a 4-year old pig organic fed")
        self.assertEqual(animal.birth_location, None)
        self.assertEqual(animal.birth_location_latitude, None)
        self.assertEqual(animal.birth_location_longitude, None)
        self.assertEqual(animal.birth_location_accuracy, MISSING)

    def test_statuses(self):
        # reload submission
        self.submission.refresh_from_db()

        # test status for submission
        self.assertEqual(self.submission.status, READY)

        # get an animal object
        animal = Animal.objects.get(pk=1)

        # test status for animal (default one)
        self.assertEqual(animal.name.status, LOADED)
