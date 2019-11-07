#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 17:14:49 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from uid.models import Submission


class BaseTestCase():
    # import this file and populate database once
    fixtures = [
        'crbanim/dictspecie',
        'crbanim/submission',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/organization',
        'uid/user',
        'language/speciesynonym'
    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission
        self.submission = Submission.objects.get(pk=1)
        self.submission_id = 1
