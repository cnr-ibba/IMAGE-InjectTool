#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 14:30:04 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import io
import json

from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from ..helpers import Auth
from ..models import ManagedTeam

from .common import BaseMixin, generate_token


class CommandsTestCase(BaseMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        # starting mocked objects
        cls.mock_auth_patcher = patch('biosample.helpers.get_manager_auth')
        cls.mock_auth = cls.mock_auth_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_auth_patcher.stop()

        # calling base method
        super().tearDownClass()

    @patch('biosample.helpers.get_manager_auth')
    def test_fill_managed(self, my_auth):
        """test fill_managed command"""

        # remove a managed team
        managed = ManagedTeam.objects.get(pk=2)
        managed.delete()

        # patch get_manager_auth value
        my_auth.return_value = Auth(
            token=generate_token(
                domains=[
                    'subs.test-team-1',
                    'subs.test-team-2',
                    'subs.test-team-3']
            )
        )

        # calling commands
        call_command('fill_managed')

        # get all managedteams object
        self.assertEqual(ManagedTeam.objects.count(), 3)
        self.assertTrue(my_auth.called)

    def test_get_json_for_biosample(self):

        args = ["--submission", 1]

        # https://stackoverflow.com/questions/4219717/how-to-assert-output-with-nosetest-unittest-in-python
        with patch('sys.stdout', new_callable=io.StringIO) as handle:
            call_command('get_json_for_biosample', *args)
            handle.seek(0)

            data = json.load(handle)
            self.assertIsInstance(data, dict)
