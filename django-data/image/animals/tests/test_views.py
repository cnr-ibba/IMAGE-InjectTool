#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 13:52:26 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.tests import (
    GeneralMixinTestCase, OwnerMixinTestCase, FormMixinTestCase,
    InvalidFormMixinTestCase)

from image_app.models import ACCURACIES, Animal

from ..views import DetailAnimalView, UpdateAnimalView
from ..forms import UpdateAnimalForm
from .common import AnimalFeaturesMixin

PRECISE = ACCURACIES.get_value('precise')
MISSING = ACCURACIES.get_value('missing')


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
        AnimalFeaturesMixin, TestCase):

    def setUp(self):
        """call base method"""

        self.description = "A new description"
        self.location = "Milano"
        self.latitude = 45.4654219
        self.longitude = 9.1859243

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


class InvalidUpdateSpeciesViewTest(
        AnimalFeaturesMixin, InvalidFormMixinTestCase, TestCase):

    def setUp(self):
        """call base method"""

        self.description = "A new description"
        self.location = "Milano"
        self.latitude = "meow"
        self.longitude = "bark"

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
