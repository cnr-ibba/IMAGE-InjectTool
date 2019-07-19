#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 10:51:40 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase

from common.constants import READY, COMPLETED, ERROR, SUBMITTED

from .common import TaskFailureMixin, RedisMixin, BaseMixin
from ..models import Submission as USISubmission, SubmissionData
from ..tasks.submission import SubmissionHelper, SplitSubmissionTask


class SplitSubmissionTaskTestCase(TaskFailureMixin, TestCase):
    def setUp(self):
        # call Mixin method
        super().setUp()

        # setting tasks
        self.my_task = SplitSubmissionTask()

        # patching objects
        self.mock_chord_patcher = patch('biosample.tasks.submission.chord')
        self.mock_chord = self.mock_chord_patcher.start()

        # other function are not called since chord is patched

    def tearDown(self):
        # stopping mock objects
        self.mock_chord_patcher.stop()

        # calling base object
        super().tearDown()

    def generic_check(self, res, n_of_submission, n_of_submissiondata):
        """Generic check for created data"""

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # get usi_submission qs
        usi_submissions_qs = USISubmission.objects.all()

        # asserting two biosample.submission data objects
        self.assertEqual(usi_submissions_qs.count(), n_of_submission)

        # assert two data for each submission
        for usi_submission in usi_submissions_qs:
            self.assertEqual(usi_submission.status, READY)

            # grab submission data queryset
            submission_data_qs = SubmissionData.objects.filter(
                submission=usi_submission)
            self.assertEqual(submission_data_qs.count(), n_of_submissiondata)

        # assert mock objects called
        self.assertTrue(self.mock_chord.called)

    # ovverride MAX_SAMPLES in order to split data
    @patch('biosample.tasks.submission.MAX_SAMPLES', 2)
    def test_split_submission(self):
        """Test splitting submission data"""

        res = self.my_task.run(submission_id=self.submission_id)

        self.generic_check(res, n_of_submission=2, n_of_submissiondata=2)

    # ovverride MAX_SAMPLES in order to split data
    @patch('biosample.tasks.submission.MAX_SAMPLES', 2)
    def test_split_submission_partial(self):
        """Test splitting submission data with some data already submitted"""

        self.name_qs.filter(pk__in=[3, 4]).update(status=COMPLETED)

        res = self.my_task.run(submission_id=self.submission_id)

        self.generic_check(res, n_of_submission=1, n_of_submissiondata=2)

    @patch('biosample.tasks.submission.MAX_SAMPLES', 2)
    def test_sample_already_in_submission(self):
        """Test splitting submission with sample in a opened submission"""

        # call task once
        self.my_task.run(submission_id=self.submission_id)

        # call a task a second time
        res = self.my_task.run(submission_id=self.submission_id)

        self.generic_check(res, n_of_submission=2, n_of_submissiondata=2)


class SubmissionHelperTestCase(BaseMixin, RedisMixin, TestCase):

    # overriding BaseMixin features
    fixtures = [
        'biosample/account',
        'biosample/managedteam',
        'biosample/submission',
        'biosample/submissiondata',
        'image_app/animal',
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
        'image_app/name',
        'image_app/ontology',
        'image_app/organization',
        'image_app/publication',
        'image_app/sample',
        'image_app/submission',
        'image_app/user'
    ]

    def setUp(self):
        # call Mixin method
        super().setUp()

        # set my pk
        self.usi_submission_id = 1

        # Instantiating SubmissionHelper with biosample.submission pk
        self.submission_helper = SubmissionHelper(self.usi_submission_id)

        # get a biosample.submission object
        self.usi_submission = USISubmission.objects.get(
            pk=self.usi_submission_id)

        # set attributes with class baseMixin class attributes for semplicity
        self.submission_helper.root = self.my_root

    def test_properties(self):
        """Asserting read properties"""

        owner = self.submission_helper.owner
        self.assertEqual(owner.username, "test")

        team_name = self.submission_helper.team_name
        self.assertEqual(team_name, "subs.test-team-1")

        self.assertIsNone(self.submission_helper.usi_submission_name)
        self.submission_helper.usi_submission_name = "test"

        self.usi_submission.refresh_from_db()
        self.assertEqual(self.usi_submission.usi_submission_name, "test")

    def test_read_token(self):
        """testing token from redis DB"""

        token = self.submission_helper.read_token()
        self.assertEqual(self.token, token)

        # assert called mock objects
        self.assertTrue(self.mock_root.called)

    @patch("biosample.tasks.submission.SubmissionHelper.read_samples")
    def test_recover_submission(self, my_helper):
        """Testing submission recover"""

        # base case: no usi_submission_name so False is expected
        self.assertFalse(self.submission_helper.recover_submission())

        # assign a usi_submission_name
        self.submission_helper.usi_submission_name = "test-submission"

        # asserted final returned status
        self.assertTrue(self.submission_helper.recover_submission())

        # assert a recovered document
        self.assertEqual(
            "test-submission",
            self.submission_helper.usi_submission.name)

        # assert get_samples called functions called
        self.assertTrue(my_helper.read_samples.called)

        # asserting others mock objects called
        self.assertFalse(self.my_root.get_team_by_name.called)
        self.assertFalse(self.my_team.create_submission.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)
        self.assertTrue(self.my_submission.propertymock.called)

    def test_create_submission(self):
        """Testing submission create"""

        self.submission_helper.create_submission()

        # assert a recovered document
        self.assertEqual(
            "new-submission",
            self.submission_helper.usi_submission.name)

        # asserting others mock objects called
        self.assertTrue(self.my_root.get_team_by_name.called)
        self.assertTrue(self.my_team.create_submission.called)
        self.assertFalse(self.my_root.get_submission_by_name.called)
        self.assertTrue(self.new_submission.propertymock.called)

    def test_start_submission(self):
        self.fail()

    def test_read_samples(self):
        self.fail()

    def test_create_or_update_sample(self):
        self.fail()

    def test_add_samples(self):
        self.fail()

    def test_mark_submission(self):
        """test adding status message to submission"""

        self.submission_helper.mark_fail(message="test")

        self.usi_submission.refresh_from_db()
        self.usi_submission.status = ERROR
        self.usi_submission.message = "test"

        self.submission_helper.mark_success()

        self.usi_submission.refresh_from_db()
        self.usi_submission.status = SUBMITTED
        self.usi_submission.message = "Submitted to biosample"
