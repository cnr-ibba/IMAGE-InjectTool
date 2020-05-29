#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 14:30:04 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import io
import json
from collections import Counter

from pyUSIrest.auth import Auth
from pyUSIrest.usi import Sample
from pyUSIrest.exceptions import USIDataError

from unittest.mock import patch, PropertyMock, Mock

from django.core.management import call_command
from django.test import TestCase

from common.constants import SUBMITTED, NEED_REVISION, ERROR

from ..models import ManagedTeam, OrphanSubmission, OrphanSample

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


class SubmitRemovalTestCase(CommandsMixin, BioSamplesMixin, TestCase):
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

        # assert sample status
        sample = OrphanSample.objects.get(pk=1)
        self.assertEqual(sample.status, SUBMITTED)

        # This was supposed to have a problem in this tests
        sample = OrphanSample.objects.get(pk=2)
        self.assertEqual(sample.status, ERROR)


class FetchRemovalTestCase(CommandsMixin, BioSamplesMixin, TestCase):
    fixtures = [
        'biosample/managedteam',
        'biosample/orphansample',
        'biosample/orphansubmission',
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

        # mocking a new submission
        self.submission = self.my_root.get_submission_by_name.return_value
        self.submission.name = "7dbb563e-c162-4df2-a48f-bbf5de8d1e35"
        self.submission.status = "Draft"

        # track a orphan submission
        self.orphan_submission_obj = OrphanSubmission.objects.get(pk=1)
        self.orphan_submission_obj.status = SUBMITTED
        self.orphan_submission_obj.save()

        # track submission in samples
        OrphanSample.objects.update(
            submission=self.orphan_submission_obj, status=SUBMITTED)

    def tearDown(self):
        self.mock_root_patcher.stop()

        super().tearDown()

    def common_tests(self, status=SUBMITTED, args=[]):
        """Assert stuff for each test"""

        # calling commands
        call_command('fetch_orphan_biosamples', *args)

        # UID submission status remain the same
        self.orphan_submission_obj.refresh_from_db()
        self.assertEqual(self.orphan_submission_obj.status, status)

        self.assertTrue(self.mock_auth.called)
        self.assertTrue(self.mock_root.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)

    def test_fetch_orphan_biosamples_pending(self):
        """test fetch_orphan_biosamples command"""

        # update submission status
        self.submission.status = 'Draft'
        self.submission.has_errors.return_value = Counter({False: 2})
        self.submission.get_status.return_value = Counter({'Pending': 2})

        # asserting things
        self.common_tests()

        # testing a not finalized biosample condition
        self.assertFalse(self.submission.finalize.called)

    def test_fetch_orphan_biosamples_complete(self):
        """test fetch_orphan_biosamples command"""

        # update submission status
        self.submission.status = 'Draft'
        self.submission.has_errors.return_value = Counter({False: 2})
        self.submission.get_status.return_value = Counter({'Complete': 2})

        # asserting things
        self.common_tests(args=['--finalize'])

        # testing a not finalized biosample condition
        self.assertTrue(self.submission.finalize.called)

    def test_fetch_orphan_biosamples_complete_ignore(self):
        """test fetch_orphan_biosamples command"""

        # update submission status
        self.submission.status = 'Draft'
        self.submission.has_errors.return_value = Counter({False: 2})
        self.submission.get_status.return_value = Counter({'Complete': 2})

        # asserting things
        self.common_tests()

        # testing a not finalized biosample condition
        self.assertFalse(self.submission.finalize.called)

    def test_fetch_orphan_biosamples_errors(self):
        """test fetch_orphan_biosamples command with issues in USI"""

        # a draft submission with errors
        self.submission.status = 'Draft'
        self.submission.has_errors.return_value = Counter(
            {True: 1, False: 1})
        self.submission.get_status.return_value = Counter({'Complete': 2})

        # Add samples. Suppose that first failed, second is ok
        my_validation_result1 = Mock()
        my_validation_result1.errorMessages = {
            'Ena': [
                'a sample message',
            ]
        }

        my_sample1 = Mock()
        my_sample1.accession = "SAMEA6376980"
        my_sample1.alias = "IMAGEA000005611"
        my_sample1.name = "test-animal"
        my_sample1.has_errors.return_value = True
        my_sample1.get_validation_result.return_value = my_validation_result1

        # sample2 is ok
        my_validation_result2 = Mock()
        my_validation_result2.errorMessages = None

        my_sample2 = Mock()
        my_sample2.accession = "SAMEA6376982"
        my_sample2.alias = "IMAGES000006757"
        my_sample2.name = "test-sample"
        my_sample2.has_errors.return_value = False
        my_sample2.get_validation_result.return_value = my_validation_result2

        # simulate that IMAGEA000000001 has errors
        self.submission.get_samples.return_value = [my_sample1, my_sample2]

        # track other objects
        self.my_sample1 = my_sample1
        self.my_sample2 = my_sample2

        # asserting things
        self.common_tests(args=['--finalize'], status=NEED_REVISION)

        # testing a not finalized biosample condition
        self.assertFalse(self.submission.finalize.called)

        # assert custom mock attributes called
        self.assertTrue(self.my_sample1.has_errors.called)
        self.assertTrue(self.my_sample1.get_validation_result.called)

        # if sample has no errors, no all methods will be called
        self.assertTrue(self.my_sample2.has_errors.called)
        self.assertFalse(self.my_sample2.get_validation_result.called)

        # assert sample status in db.
        sample = OrphanSample.objects.get(pk=1)
        self.assertEqual(sample.status, SUBMITTED)

        # Same logic of FetchStatusHelper
        sample = OrphanSample.objects.get(pk=2)
        self.assertEqual(sample.status, NEED_REVISION)
