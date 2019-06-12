#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 14:30:04 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from common.constants import SUBMITTED
from image_app.models import Name

from ..models import ManagedTeam

from .common import SubmitMixin


class CommandsTestCase(SubmitMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        unmanaged = ManagedTeam.objects.get(pk=2)
        unmanaged.delete()

        # starting mocked objects
        cls.mock_root_patcher = patch('pyUSIrest.client.Root')
        cls.mock_root = cls.mock_root_patcher.start()

        cls.mock_auth_patcher = patch('biosample.helpers.Auth')
        cls.mock_auth = cls.mock_auth_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_root_patcher.stop()
        cls.mock_auth_patcher.stop()

        # calling base method
        super().tearDownClass()

    def test_biosample_submission(self):
        "Test biosample_submission command command."

        # mocking objects
        args = ["--submission", 1]
        opts = {}
        call_command('biosample_submit', *args, **opts)

        # reload submission
        self.submission_obj.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission_obj.status, SUBMITTED)
        self.assertEqual(
            self.submission_obj.message,
            "Waiting for biosample validation")
        self.assertEqual(
            self.submission_obj.biosample_submission_id,
            "new-submission")

        # check name status changed
        qs = Name.objects.filter(status=SUBMITTED)
        self.assertEqual(len(qs), self.n_to_submit)

        # assert called mock objects
        self.assertTrue(self.mock_root.called)
        self.assertTrue(self.my_root.get_team_by_name.called)
        self.assertTrue(self.my_team.create_submission.called)
        self.assertFalse(self.my_root.get_submission_by_name.called)
        self.assertEqual(
            self.new_submission.create_sample.call_count, self.n_to_submit)
        self.assertFalse(self.new_submission.propertymock.called)
