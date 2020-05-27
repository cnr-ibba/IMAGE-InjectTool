#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 14:30:04 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import io
import json

from pyUSIrest.auth import Auth
from pyUSIrest.usi import Sample
from pyUSIrest.exceptions import USIDataError

from unittest.mock import patch, PropertyMock

from django.core.management import call_command
from django.test import TestCase

from common.constants import SUBMITTED

from ..models import ManagedTeam, OrphanSubmission

from .common import BaseMixin, generate_token, BioSamplesMixin


class CommandsMixin():
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


class CommandsTestCase(CommandsMixin, BaseMixin, TestCase):
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


class BioSampleRemovalTestCase(CommandsMixin, BioSamplesMixin, TestCase):
    fixtures = [
        'biosample/managedteam',
        'biosample/orphansample',
        'uid/dictspecie',
    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # starting mocked objects
        self.mock_root_patcher = patch('pyUSIrest.usi.Root')
        self.mock_root = self.mock_root_patcher.start()

        # start root object
        self.my_root = self.mock_root.return_value

        # mocking chain
        self.my_team = self.my_root.get_team_by_name.return_value
        self.my_team.name = "subs.test-team-1"

        # mocking a new submission
        self.new_submission = self.my_team.create_submission.return_value
        self.new_submission.name = "new-submission"

        # set status. Because of the way mock attributes are stored you can’t
        # directly attach a PropertyMock to a mock object. Instead you can
        # attach it to the mock type object:
        self.new_submission.propertymock = PropertyMock(return_value='Draft')
        type(self.new_submission).status = self.new_submission.propertymock

    def tearDown(self):
        self.mock_root_patcher.stop()

        super().tearDown()

    @patch('biosample.helpers.get_manager_auth')
    def test_patch_orphan_biosamples(self, my_auth):
        """test patch_orphan_biosamples command"""

        # patch get_manager_auth value
        my_auth.return_value = Auth(
            token=generate_token()
        )

        # mocking sample creation: two objects: one submitted, one not
        self.new_submission.create_sample.side_effect = [
            Sample(auth=generate_token()),
            USIDataError("test")
        ]

        # calling commands
        call_command('patch_orphan_biosamples')

        # assert a submission created
        self.assertTrue(my_auth.called)
        self.assertTrue(self.my_team.create_submission.called)
        self.assertTrue(self.new_submission.create_sample.called)

        # check for an object into database
        submissions = OrphanSubmission.objects.all()
        self.assertEqual(len(submissions), 1)

        # test submission attributes
        submission = submissions[0]
        self.assertEqual(submission.usi_submission_name, "new-submission")
        self.assertEqual(submission.samples_count, 1)
        self.assertEqual(submission.status, SUBMITTED)
