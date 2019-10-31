#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 16:00:29 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse

from uid.models import Animal, Sample
from validation.models import ValidationResult
from common.tests import MessageMixinTestCase

from .common import (
    AnimalFeaturesMixin, AnimalViewTestMixin, AnimalStatusMixin, READY)
from ..views import DeleteAnimalView


class DeleteAnimalViewTest(
        AnimalViewTestMixin, TestCase):

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

        self.url = reverse("animals:delete", kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/animals/1/delete/')
        self.assertIsInstance(view.func.view_class(), DeleteAnimalView)

    def test_reload_not_found_status_code(self):
        url = reverse('animals:delete', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_navigation_links(self):
        """Testing link to a javascript function"""

        link = "javascript:{goBack()}"
        self.assertContains(self.response, 'href="{0}"'.format(link))

    def test_name_data(self):
        """Test delete animal show this sample"""

        # test for animal name in submission
        names = ['Siems_0722_393449']

        for name in names:
            self.assertContains(self.response, name)


class DeleteAnimalViewStatusesTest(
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
        self.url = reverse("animals:delete", kwargs={'pk': 1})
        self.redirect_url = self.animal.get_absolute_url()


# Here, I'm already tested the urls, csfr. So BaseTest
class SuccessfulDeleteAnimalViewTest(
        AnimalFeaturesMixin, MessageMixinTestCase, TestCase):

    def setUp(self):
        """call base method"""

        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        # get objects
        animal = Animal.objects.get(pk=1)
        self.submission = animal.submission

        # update submission status (to get this url)
        self.submission.status = READY
        self.submission.save()

        # create a new child for this animal
        self.child = self.create_child()

        # count number of objects
        self.n_of_animals = Animal.objects.count()
        self.n_of_samples = Sample.objects.count()

        self.url = reverse("animals:delete", kwargs={'pk': 1})
        self.response = self.client.post(
            self.url,
            {},
            follow=True
        )

    def create_child(self):
        """Create a new child animal for testing purpose"""

        # choose mother and father
        father = Animal.objects.get(name='ANIMAL:::ID:::132713')
        mother = Animal.objects.get(name='ANIMAL:::ID:::mother')

        # create an animal object from an existing one
        animal = Animal.objects.get(pk=1)

        # create a new animal from animal
        animal.pk = None
        animal.name = "test child"
        animal.father = father
        animal.mother = mother
        animal.save()

        return animal

    def test_redirect(self):
        url = reverse('submissions:edit', kwargs={'pk': self.submission.pk})
        self.assertRedirects(self.response, url)

    def test_animal_delete(self):
        """Deleting an animal will delete its samples and
        validationresults. Its child will be present"""

        # three animals present (see uid fixtures)
        n_animals = Animal.objects.count()
        self.assertEqual(n_animals, self.n_of_animals-1)

        # refresh child item from db
        self.child.refresh_from_db()

        # assert child father and mother
        self.assertIsNone(self.child.father)
        mother = Animal.objects.get(name='ANIMAL:::ID:::unknown_dam')
        self.assertEqual(self.child.mother, mother)

        # now its samples (the sample related to deleted animal was deleted)
        n_samples = Sample.objects.count()
        self.assertEqual(n_samples, self.n_of_samples-1)

        # check for ramaining names
        names = [animal.name for animal in Animal.objects.all()]
        self.assertIn("ANIMAL:::ID:::unknown_sire", names)
        self.assertIn("ANIMAL:::ID:::unknown_dam", names)
        self.assertIn("test child", names)

        # check for validationresults
        n_validation = ValidationResult.objects.count()
        self.assertEqual(n_validation, 0)

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
