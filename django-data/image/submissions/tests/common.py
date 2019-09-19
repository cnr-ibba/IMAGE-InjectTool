#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 16:25:39 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os

from django.test import Client

import common.tests
from image_app.models import Submission

from common.constants import (
    WAITING, LOADED, ERROR, READY, NEED_REVISION, SUBMITTED, COMPLETED,
    CRYOWEB_TYPE, CRB_ANIM_TYPE, TEMPLATE_TYPE)


class SubmissionFormMixin():

    data_sources_files = {
        CRYOWEB_TYPE: "cryoweb_test_data_only.sql",
        CRB_ANIM_TYPE: "crbanim_test_data.csv",
        "latin_type": "crbanim_test_data_latin-1.csv",
        TEMPLATE_TYPE: "Image_sample_template_with_example_20190405.xlsx",
        "not_valid_crbanim": "Mapping_rules_CRB-Anim_InjectTool_v1.csv"
    }

    data_sources_types = {
        CRYOWEB_TYPE: CRYOWEB_TYPE,
        CRB_ANIM_TYPE: CRB_ANIM_TYPE,
        "latin_type": CRB_ANIM_TYPE,
        TEMPLATE_TYPE: TEMPLATE_TYPE,
        "not_valid_crbanim": CRB_ANIM_TYPE
    }

    def get_data(self, ds_file=CRYOWEB_TYPE):
        """Get data dictionary"""

        # get ds_type reling on ds_file
        ds_type = self.data_sources_types[ds_file]

        # get data source path relying on type
        ds_path = os.path.join(
            common.tests.__path__[0],
            self.data_sources_files[ds_file]
        )

        return ds_type, ds_path


class SubmissionStatusMixin():
    """Test response with different submission statuses"""

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


class SubmissionDataMixin():
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
        'image_app/user',
        'validation/validationsummary',
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        # get a submission object
        self.submission = Submission.objects.get(pk=1)
