#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 12:59:41 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse
from django.utils.http import urlquote

from common.constants import NEED_REVISION
from common.tests import GeneralMixinTestCase, OwnerMixinTestCase
from image_app.models import Submission

from ..views import EditSubmissionView
from .common import SubmissionStatusMixin


class EditSubmissionViewTest(
        GeneralMixinTestCase, OwnerMixinTestCase, TestCase):

    fixtures = [
        'image_app/animal',
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
        'image_app/name',
        'image_app/organization',
        'image_app/publication',
        'image_app/sample',
        'image_app/submission',
        'image_app/user'
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        # get a submission object
        self.submission = Submission.objects.get(pk=1)

        # update submission status with a permitted statuses
        self.submission.status = NEED_REVISION
        self.submission.save()

        self.url = reverse('submissions:edit', kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/edit/')
        self.assertIsInstance(view.func.view_class(), EditSubmissionView)

    def test_edit_not_found_status_code(self):
        url = reverse('submissions:edit', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_contains_navigation_links(self):
        """Contain links to ListSpeciesView, and submissions links"""

        country = urlquote("United Kingdom")
        link = reverse("language:species") + "?country=%s" % country
        self.assertContains(self.response, 'href="{0}"'.format(link))

        detail_url = reverse('submissions:detail', kwargs={'pk': 1})
        list_url = reverse('submissions:list')
        dashboard_url = reverse('image_app:dashboard')

        self.assertContains(self.response, 'href="{0}"'.format(detail_url))
        self.assertContains(self.response, 'href="{0}"'.format(list_url))
        self.assertContains(self.response, 'href="{0}"'.format(dashboard_url))

    def test_name_data(self):
        """Test submission has data"""

        # test for animal name in submission
        names = ['ANIMAL:::ID:::132713', 'Siems_0722_393449']

        for name in names:
            self.assertContains(self.response, name)

        # unknown animals should be removed from a submission
        names = ['ANIMAL:::ID:::unknown_sire', 'ANIMAL:::ID:::unknown_dam']

        for name in names:
            self.assertNotContains(self.response, name)

    def test_name_urls(self):
        """Test data has links for delete and update"""

        animal_update_url = reverse('animals:update', kwargs={'pk': 1})
        animal_delete_url = reverse('animals:delete', kwargs={'pk': 1})

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    animal_update_url))

        self.assertContains(
            self.response,
            'href="{0}"'.format(
                    animal_delete_url))

        # TODO: test for samples Update/Delete Views


class EditSubmissionViewStatusesTest(SubmissionStatusMixin, TestCase):
    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission"
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url = reverse('submissions:edit', kwargs={'pk': 1})

        # get a submission object
        self.submission = Submission.objects.get(pk=1)
        self.redirect_url = self.submission.get_absolute_url()
