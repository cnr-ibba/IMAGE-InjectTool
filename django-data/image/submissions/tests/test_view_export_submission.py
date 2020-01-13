#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 13 12:22:34 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import itertools

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.constants import NEED_REVISION
from common.tests import GeneralMixinTestCase, OwnerMixinTestCase
from uid.models import Submission

from ..views import ExportSubmissionView


class ExportSubmissionViewTest(
        GeneralMixinTestCase, OwnerMixinTestCase, TestCase):

    fixtures = [
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user'
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

        self.url = reverse('submissions:export', kwargs={'pk': 1})
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/submissions/1/export/')
        self.assertIsInstance(view.func.view_class(), ExportSubmissionView)

    def test_edit_not_found_status_code(self):
        url = reverse('submissions:export', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_file_attachment(self):
        # https://stackoverflow.com/a/8244317/4385116
        self.assertEqual(
            self.response.get('Content-Disposition'),
            'attachment; filename="somefilename.csv"'
        )

        # https://docs.djangoproject.com/en/dev/ref/request-response/#streaminghttpresponse-objects
        self.assertIn(b'Row 0,0\r\n', itertools.islice(
                self.response.streaming_content, 5))
