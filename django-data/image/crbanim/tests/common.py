#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 17:14:49 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from common.tests import DataSourceMixinTestCase
from image_app.models import Submission


class BaseTestCase(DataSourceMixinTestCase):
    # define attribute in DataSourceMixinTestCase
    model = Submission

    # import this file and populate database once
    fixtures = [
        'crbanim/dictspecie',
        'crbanim/submission',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/organization',
        'image_app/user'
    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission
        self.submission = Submission.objects.get(pk=1)
