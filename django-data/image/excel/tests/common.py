#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 10:57:13 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from common.tests import DataSourceMixinTestCase
from image_app.models import Submission


class BaseExcelMixin(DataSourceMixinTestCase):
    # define attribute in DataSourceMixinTestCase
    model = Submission

    # import this file and populate database once
    fixtures = [
        'excel/submission',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/organization',
        'image_app/user',
        'language/dictspecie',
        'language/speciesynonym',
    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission
        self.submission = Submission.objects.get(pk=1)
        self.submission_id = 1
