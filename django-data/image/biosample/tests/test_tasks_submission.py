#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 10:51:40 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch, PropertyMock, Mock

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

    @patch.object(SubmissionHelper, "read_samples")
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
        self.assertTrue(my_helper.called)

        # asserting others mock objects called
        self.assertFalse(self.my_root.get_team_by_name.called)
        self.assertFalse(self.my_team.create_submission.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)
        self.assertTrue(self.my_submission.propertymock.called)

    def test_recover_submission_error(self):
        """Testing submission recover for a closed submission"""

        # assign a usi_submission_name
        self.submission_helper.usi_submission_name = "test-submission"

        # change submission status
        self.my_submission.propertymock = PropertyMock(
            return_value='Completed')
        type(self.my_submission).status = self.my_submission.propertymock

        self.assertRaisesRegex(
            Exception,
            "Cannot recover submission",
            self.submission_helper.recover_submission)

        # asserting others mock objects called
        self.assertFalse(self.my_root.get_team_by_name.called)
        self.assertFalse(self.my_team.create_submission.called)
        self.assertTrue(self.my_root.get_submission_by_name.called)
        self.assertTrue(self.my_submission.propertymock.called)

    def test_create_submission(self):
        """Testing submission create"""

        self.submission_helper.create_submission()

        # assert a new document
        self.assertEqual(
            "new-submission",
            self.submission_helper.usi_submission.name)

        # asserting others mock objects called
        self.assertTrue(self.my_root.get_team_by_name.called)
        self.assertTrue(self.my_team.create_submission.called)
        self.assertFalse(self.my_root.get_submission_by_name.called)

    @patch.object(SubmissionHelper, "create_submission")
    @patch.object(SubmissionHelper, "recover_submission")
    def test_start_submission(self, my_recover, my_create):
        """testing start a submission"""

        def create_submission():
            """Simulate create submission (already tested)"""

            self.submission_helper.usi_submission = self.new_submission
            return self.new_submission

        my_recover.return_value = False
        my_create.side_effect = create_submission

        usi_submission = self.submission_helper.start_submission()

        # assert a new document
        self.assertEqual("new-submission", usi_submission.name)

        # assert mock methods called
        self.assertTrue(my_recover.called)
        self.assertTrue(my_create.called)

    def test_read_samples(self):

        # creating mock samples
        my_samples = [
            Mock(**{'alias': 'IMAGEA000000001',
                    'title': 'a 4-year old pig organic fed'}),
            Mock(**{'alias': 'IMAGES000000001',
                    'title': 'semen collected when the animal turns to 4'}),
        ]

        # mocking set samples
        self.my_submission.get_samples.return_value = my_samples
        self.submission_helper.usi_submission = self.my_submission

        # calling function
        submitted_samples = self.submission_helper.read_samples()

        self.assertIsInstance(submitted_samples, dict)
        self.assertEqual(len(submitted_samples), 2)

        keys = submitted_samples.keys()
        self.assertIn('IMAGEA000000001', keys)
        self.assertIn('IMAGES000000001', keys)

    def test_create_sample(self):
        # get a model object
        submission_data = SubmissionData.objects.get(pk=1)
        model = submission_data.content_object

        # get a biosample submission
        self.submission_helper.usi_submission = self.my_submission

        # add model to biosample submission
        self.submission_helper.create_or_update_sample(model)

        # testing things
        self.assertEqual(
            self.my_submission.create_sample.call_count, 1)

    def test_update_sample(self):
        # creating mock samples
        my_samples = [
            Mock(**{'alias': 'IMAGEA000000001',
                    'title': 'a 4-year old pig organic fed'}),
        ]

        # mocking set samples
        self.my_submission.get_samples.return_value = my_samples
        self.submission_helper.usi_submission = self.my_submission

        # read samples through function (already tested)
        self.submission_helper.read_samples()

        # get a model object
        submission_data = SubmissionData.objects.get(pk=1)
        model = submission_data.content_object

        # add model to biosample submission
        self.submission_helper.create_or_update_sample(model)

        # testing patch
        for sample in my_samples:
            self.assertTrue(sample.patch.called)

    @patch.object(SubmissionHelper, "create_or_update_sample")
    def test_add_samples(self, my_create):
        """Test adding samples"""

        # simulate a submission recover: mark an animal as already submitted
        submission_data = SubmissionData.objects.get(pk=1)
        submission_data.content_object.name.status = SUBMITTED
        submission_data.content_object.name.save()

        # calling method
        self.submission_helper.add_samples()

        # assert create sample in biosample called once
        my_create.assert_called_once()

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
