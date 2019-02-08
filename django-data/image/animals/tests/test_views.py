#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 13:52:26 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.tests import GeneralMixinTestCase, OwnerMixinTestCase

from ..views import DetailAnimalView
from .common import AnimalFeaturesMixin


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
