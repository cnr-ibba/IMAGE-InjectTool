#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 11:17:12 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.core.management import call_command
from django.test import TestCase

from common.constants import LOADED
from common.tests import WebSocketMixin
from uid.models import Submission, Animal, Sample


class CommandsTestCase(WebSocketMixin, TestCase):
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

        # check Animal status changed
        qs = Animal.objects.filter(submission=submission_obj)

        for model in qs:
            self.assertEqual(model.status, LOADED)

        # check sample status changed
        qs = Sample.objects.filter(submission=submission_obj)

        for model in qs:
            self.assertEqual(model.status, LOADED)

        self.check_message(
            message='Loaded',
            notification_message="Submission reset to 'Loaded' state")
