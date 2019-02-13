#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 12:59:41 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse
from django.utils.http import urlquote

from common.tests import GeneralMixinTestCase, OwnerMixinTestCase
from image_app.models import Submission, STATUSES

from ..views import EditSubmissionView

WAITING = STATUSES.get_value('waiting')
LOADED = STATUSES.get_value('loaded')
ERROR = STATUSES.get_value('error')
READY = STATUSES.get_value('ready')
NEED_REVISION = STATUSES.get_value('need_revision')
SUBMITTED = STATUSES.get_value('submitted')
COMPLETED = STATUSES.get_value('completed')


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


class EditSubmissionViewStatusesTest(TestCase):
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

    def test_waiting(self):
        """Test waiting statuses return to submission detail"""

        # update statuses
        self.submission.status = WAITING
        self.submission.save()

        # test redirect
        response = self.client.get(self.url)
        self.assertRedirects(response, self.redirect_url)

    def test_loaded(self):
        """Test loaded status"""

        # force submission status
        self.submission.status = LOADED
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_submitted(self):
        """Test submitted status"""

        # force submission status
        self.submission.status = SUBMITTED
        self.submission.save()

        # test redirect
        response = self.client.get(self.url)
        self.assertRedirects(response, self.redirect_url)

    def test_error(self):
        """Test error status"""

        # force submission status
        self.submission.status = ERROR
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_need_revision(self):
        """Test need_revision status"""

        # force submission status
        self.submission.status = NEED_REVISION
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_ready(self):
        """Test ready status"""

        # force submission status
        self.submission.status = READY
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_completed(self):
        """Test completed status"""

        # force submission status
        self.submission.status = COMPLETED
        self.submission.save()

        # test no redirect
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
