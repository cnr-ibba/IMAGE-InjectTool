#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 15:49:18 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from common.constants import ERROR
from common.tests import DataSourceMixinTestCase
from image_app.models import Submission, db_has_data

from ..helpers import upload_crbanim, CRBAnimImportError


class BaseTestCase():
    # import this file and populate database once
    fixtures = [
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/organization',
        'crbanim/submission',
        'image_app/user',
        'language/dictspecie',
        'language/speciesynonim'
    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission
        self.submission = Submission.objects.get(pk=1)


class UploadCRBAnim(DataSourceMixinTestCase, BaseTestCase, TestCase):
    # define attribute in DataSourceMixinTestCase
    model = Submission

    def test_upload_crbanim(self):
        """Testing uploading and importing data from crbanim to UID"""

        self.assertTrue(upload_crbanim(self.submission.id))
        self.assertTrue(db_has_data())
