#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 13 12:22:34 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

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
            'attachment; filename="submission_1_names.csv"'
        )

    def test_file_content(self):
        reference = [
            b'id,name,biosample_id,material,status,last_changed,'
            b'last_submitted\r\n',
            b'3,ANIMAL:::ID:::son,,Organism,Loaded,,\r\n',
            b'2,ANIMAL:::ID:::mother,,Organism,Loaded,,\r\n',
            b'1,ANIMAL:::ID:::132713,,Organism,Loaded,,\r\n',
            b'1,Siems_0722_393449,,Specimen from Organism,Loaded,,\r\n',
        ]

        # https://docs.djangoproject.com/en/dev/ref/request-response/#streaminghttpresponse-objects
        test = list(self.response.streaming_content)

        self.assertListEqual(sorted(reference), sorted(test))
