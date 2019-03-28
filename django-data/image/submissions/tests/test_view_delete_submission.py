#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 16:01:55 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.constants import READY
from common.tests.mixins import (
    GeneralMixinTestCase, OwnerMixinTestCase, MessageMixinTestCase)
from image_app.models import Submission, Animal, Sample, Name

from ..views import DeleteSubmissionView
from .common import SubmissionStatusMixin


class SubmissionDeleteMixin():
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

        # define url
        self.url = reverse('submissions:delete', kwargs={'pk': 1})


class DeleteSubmissionViewTest(
        SubmissionDeleteMixin, GeneralMixinTestCase, OwnerMixinTestCase,
        TestCase):

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
        # call base method
        super().setUp()

        # update submission status (to get this url)
        self.submission.status = READY
        self.submission.save()

        # get response (no post request)
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/delete/')
        self.assertIsInstance(view.func.view_class(), DeleteSubmissionView)

    def test_reload_not_found_status_code(self):
        url = reverse('submissions:delete', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_navigation_links(self):
        """Testing link to submission detail"""

        link = reverse('submissions:detail', kwargs={'pk': 1})
        self.assertContains(self.response, 'href="{0}"'.format(link))

    def test_related_items(self):
        """Test delete animal show this sample"""

        # test for displayed items
        names = ['Animals', 'Samples']

        for name in names:
            self.assertContains(self.response, name)


class DeleteSubmissionViewStatusesTest(
        SubmissionDeleteMixin, SubmissionStatusMixin, TestCase):
    """Test page access with different submission status"""

    def setUp(self):
        # call base method
        super().setUp()

        # get redirect url
        self.redirect_url = self.submission.get_absolute_url()


# Here, I'm already tested the urls, csfr. So BaseTest
class SuccessfulDeleteSubmissionViewTest(
        SubmissionDeleteMixin, MessageMixinTestCase, TestCase):

    def setUp(self):
        """call base method"""

        # call base method
        super().setUp()

        # update submission status (to delete this submission)
        self.submission.status = READY
        self.submission.save()

        # get a response
        self.response = self.client.post(
            self.url,
            {},
            follow=True
        )

    def test_redirect(self):
        url = reverse('image_app:dashboard')
        self.assertRedirects(self.response, url)

    def test_delete(self):
        """Deleting a submission will delete Animal, Samples and Names"""

        # One animal present
        n_animals = Animal.objects.count()
        self.assertEqual(n_animals, 0)

        # nor its samples
        n_samples = Sample.objects.count()
        self.assertEqual(n_samples, 0)

        # names will be deleted
        n_names = Name.objects.count()
        self.assertEqual(n_names, 0)

        # check submission objects
        n_submissions = Submission.objects.count()
        self.assertEqual(n_submissions, 0)

    def test_message(self):
        """Assert 'successfully deleted' message"""

        # check messages (defined in common.tests.MessageMixinTestCase
        self.check_messages(
            self.response,
            "info",
            "was successfully deleted")
