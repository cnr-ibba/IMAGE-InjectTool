#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 11:17:12 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.core.management import call_command
from django.test import TestCase

from common.constants import LOADED
from image_app.models import Submission, Name


class CommandsTestCase(TestCase):
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

    def test_reset_submission(self):
        "Test biosample_submission command command."

        # mocking objects
        args = ["--submission", 1]
        opts = {}
        call_command('reset_submission', *args, **opts)

        # get submission
        submission_obj = Submission.objects.get(pk=1)

        # check submission.state changed
        self.assertEqual(submission_obj.status, LOADED)

        # check name status changed
        qs = Name.objects.filter(submission=submission_obj)

        for name in qs:
            self.assertEqual(name.status, LOADED)
