#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 10:51:40 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch, PropertyMock, Mock, call

from django.test import TestCase
from django.core import mail

from common.constants import (
    READY, COMPLETED, ERROR, SUBMITTED, WAITING, STATUSES)

from .common import TaskFailureMixin, RedisMixin, BaseMixin
from ..models import Submission as USISubmission, SubmissionData
from ..tasks.submission import (
    SubmissionHelper, SplitSubmissionTask, SubmitTask, SubmissionError,
    SubmissionCompleteTask)


class SubmissionFeaturesMixin(BaseMixin):
    """Common features for SubmitTask and SubmissionHelper"""

    # overriding BaseMixin features
    fixtures = [
        'biosample/account',
        'biosample/managedteam',
        'biosample/submission',
        'biosample/submissiondata',
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/ontology',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user'
    ]


class SplitSubmissionMixin(TaskFailureMixin, BaseMixin):
    """Generic stuff for SplitSubmissionTask tests"""

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


class SplitSubmissionTaskTestCase(SplitSubmissionMixin, TestCase):
    # ovverride MAX_SAMPLES in order to split data
    @patch('biosample.tasks.submission.MAX_SAMPLES', 2)
    def test_split_submission(self):
        """Test splitting submission data"""

        res = self.my_task.run(submission_id=self.submission_id)

        self.generic_check(res, n_of_submission=2, n_of_submissiondata=2)
        self.assertEqual(self.n_to_submit, SubmissionData.objects.count())

    # ovverride MAX_SAMPLES in order to split data
    @patch('biosample.tasks.submission.MAX_SAMPLES', 2)
    def test_split_submission_partial(self):
        """Test splitting submission data with some data already submitted"""

        self.animal_qs.filter(pk=1).update(status=COMPLETED)
        self.sample_qs.filter(pk=1).update(status=COMPLETED)

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


class SplitSubmissionTaskUpdateTestCase(
        SubmissionFeaturesMixin, SplitSubmissionMixin, TestCase):
    """
    A particoular test case: I submit data once and then biosample tell me
    that there are errors in submission data. So I mark name with need revision
    status and the submission is already opened. I can't send data within a
    new submission, I need to restore things and submit the data I have (since
    to_biosample() is called on user data when submitting, there are no issues
    with old data in biosample.models)"""

    def setUp(self):
        # call Mixin method
        super().setUp()

        # ok in this case, my uid.Samples are READY since I passed validation
        # after fail into biosample stage. My biosample.submission will be in
        # ERROS or NEED_REVISION since is the last status I saw
        USISubmission.objects.update(status=ERROR)

    # ovverride MAX_SAMPLES in order to split data
    @patch('biosample.tasks.submission.MAX_SAMPLES', 2)
    def test_split_submission(self):
        """Test splitting submission data"""

        res = self.my_task.run(submission_id=self.submission_id)

        self.generic_check(res, n_of_submission=2, n_of_submissiondata=2)
        self.assertEqual(self.n_to_submit, SubmissionData.objects.count())

    # ovverride MAX_SAMPLES in order to split data
    @patch('biosample.tasks.submission.MAX_SAMPLES', 2)
    def test_split_submission_issues(self):
        """Test splitting submission data with issues"""

        # add a new submission data with the same sample, just to test
        # exception handling
        # https://stackoverflow.com/a/4736172/4385116
        submission_data = SubmissionData.objects.get(pk=1)
        submission_data.pk = None
        submission_data.save()

        self.assertRaisesRegex(
            SubmissionError,
            "More than one submission opened",
            self.my_task.run,
            submission_id=self.submission_id)


class SubmissionHelperTestCase(RedisMixin, SubmissionFeaturesMixin, TestCase):

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
            SubmissionError,
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

        # assert status
        self.assertEqual(model.status, SUBMITTED)

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

        # assert status
        self.assertEqual(model.status, SUBMITTED)

        # testing patch
        for sample in my_samples:
            self.assertTrue(sample.patch.called)

    @patch.object(SubmissionHelper, "create_or_update_sample")
    def test_add_one_sample(self, my_create):
        """Test adding one sample"""

        # simulate a submission recover: mark an animal as already submitted
        submission_data = SubmissionData.objects.get(pk=1)
        submission_data.content_object.status = SUBMITTED
        submission_data.content_object.save()

        # calling method
        self.submission_helper.add_samples()

        # assert create sample in biosample called once
        my_create.assert_called_once()

    @patch.object(SubmissionHelper, "create_or_update_sample")
    def test_add_samples(self, my_create):
        """Test adding samples in correct order"""

        # getting submission data an mock called arguments
        data = list(self.usi_submission.submission_data.order_by('id'))
        data = [call(el.content_object) for el in data]

        # calling method
        self.submission_helper.add_samples()

        # assert num called and arguments
        self.assertEqual(my_create.call_count, 2)
        self.assertEqual(my_create.call_args_list, data)

    @patch.object(SubmissionHelper, "create_or_update_sample")
    def test_add_samples_order(self, my_create):
        """Test adding samples in different order"""

        # now create another animal object as a copy of the previous one
        # and save it into database,
        el = self.usi_submission.submission_data.order_by('id').first()
        el.pk = None
        el.save()

        # remove the first and check that order is maintaned
        self.usi_submission.submission_data.order_by('id').first().delete()

        # getting submission data an mock called arguments
        data = list(self.usi_submission.submission_data.order_by('id'))
        data = [call(el.content_object) for el in data]

        # calling method
        self.submission_helper.add_samples()

        # assert num called and arguments
        self.assertEqual(my_create.call_count, 2)
        self.assertEqual(my_create.call_args_list, data)

    def test_mark_submission(self):
        """test adding status message to submission"""

        self.submission_helper.mark_fail(message="test")

        self.usi_submission.refresh_from_db()
        self.assertEqual(self.usi_submission.status, ERROR)
        self.assertEqual(self.usi_submission.message, "test")

        self.submission_helper.mark_success()

        self.usi_submission.refresh_from_db()
        self.assertEqual(self.usi_submission.status, SUBMITTED)
        self.assertEqual(
            self.usi_submission.message,
            "Waiting for biosample validation")


class SubmitTaskTestCase(SubmissionFeaturesMixin, TestCase):
    """Test submission task"""

    def setUp(self):
        # call Mixin method
        super().setUp()

        # setting tasks
        self.my_task = SubmitTask()

        # set my pk
        self.usi_submission_id = 1

        # get a biosample.submission object
        self.usi_submission = USISubmission.objects.get(
            pk=self.usi_submission_id)

        # starting mocked objects
        self.mock_read_patcher = patch.object(SubmissionHelper, "read_token")
        self.mock_read = self.mock_read_patcher.start()

        self.mock_start_patcher = patch.object(
            SubmissionHelper, "start_submission")
        self.mock_start = self.mock_start_patcher.start()

        self.mock_add_patcher = patch.object(SubmissionHelper, "add_samples")
        self.mock_add = self.mock_add_patcher.start()

    def tearDown(self):
        # stopping mock objects
        self.mock_read_patcher.stop()
        self.mock_start_patcher.stop()
        self.mock_add_patcher.stop()

        # calling base object
        super().tearDown()

    def common_test(self, task_result, message, status):
        # assert a success with data uploading
        self.assertEqual(task_result, ("success", self.usi_submission_id))

        # check submission status and message
        self.usi_submission.refresh_from_db()

        # check submission.status changed
        self.assertEqual(self.usi_submission.status, status)
        self.assertIn(message, self.usi_submission.message)

        # no status changes for UID submission (will callback change status)
        self.assertEqual(self.submission_obj.status, WAITING)
        self.assertEqual(
            self.submission_obj.message,
            "Waiting for biosample submission")

        self.assertTrue(self.mock_read.called)
        self.assertTrue(self.mock_start.called)
        self.assertTrue(self.mock_add.called)

    def test_submit(self):
        """Test submitting into biosample"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        # Remeber that submission_id will be biosample.models.Submission.id
        res = self.my_task.run(usi_submission_id=self.usi_submission_id)

        self.common_test(res, "Waiting for biosample validation", SUBMITTED)

    def test_issues_with_api(self):
        """Test errors with submission API"""

        # Set a side effect on the patched methods
        # so that they raise the errors we want.
        self.mock_add.side_effect = ConnectionError()

        # call task. No retries with issues at EBI
        res = self.my_task.run(usi_submission_id=self.usi_submission_id)

        # this is the message I want
        message = "Errors in EBI API endpoints. Please try again later"

        # assert anyway a success
        self.common_test(res, message, READY)

    def test_token_expired(self):
        """Testing token expiring during a submission"""

        # simulating a token expiring during a submission
        self.mock_add.side_effect = RuntimeError("Your token is expired")

        # calling task
        res = self.my_task.run(usi_submission_id=self.usi_submission_id)

        message = (
            "Your token is expired: please submit again to resume submission")

        # assert anyway a success
        self.common_test(res, message, READY)

    def test_unmanaged(self):
        """Testing unmanaged Exception"""

        # simulating a token expiring during a submission
        self.mock_add.side_effect = Exception("Unmanaged")

        # calling task
        res = self.my_task.run(usi_submission_id=self.usi_submission_id)

        message = "Exception: Unmanaged"

        # assert anyway a success
        self.common_test(res, message, ERROR)


class SubmissionCompleteTaskTestCase(
        SubmissionFeaturesMixin, TaskFailureMixin, BaseMixin, TestCase):

    """Test class for SubmissionCompleteTask"""

    def setUp(self):
        # call Mixin method
        super().setUp()

        # setting tasks
        self.my_task = SubmissionCompleteTask()

        # these will be the tasks arguments, indipendently by status etc
        self.my_tasks_args = ([("success", 1), ("success", 2)], )

        # update statuses for biosample.models.Submission
        USISubmission.objects.update(
            status=SUBMITTED,
            message='Waiting for biosample validation')

    def common_check(self, status, message, update_db=True):
        """Common check for tests"""

        # update an object
        if update_db:
            usi_submission = USISubmission.objects.get(pk=1)
            usi_submission.status = status
            usi_submission.message = message
            usi_submission.save()

        # calling task
        result = self.my_task.run(
            *self.my_tasks_args,
            uid_submission_id=self.submission_id)

        # assert a success with data uploading
        self.assertEqual(result, "success")

        # check status and messages
        self.submission_obj.refresh_from_db()
        self.assertEqual(self.submission_obj.status, status)
        self.assertEqual(self.submission_obj.message, message)

        # calling a WebSocketMixin method
        self.check_message(
            STATUSES.get_value_display(status),
            message)

    def test_submission_complete(self):
        """test no issues after a submission"""

        self.common_check(
            SUBMITTED,
            'Waiting for biosample validation')

    def test_empty_submission(self):
        """An empty submission is marked as COMPLETED"""

        # delete USISubmission objects
        USISubmission.objects.all().delete()

        # updating task args like a result for an empty submission
        self.my_tasks_args = ([], )

        # check status and messages
        status = ERROR
        message = "Submission %s is empty!" % self.submission_obj
        self.common_check(status, message, update_db=False)

    def test_error_api_endpoint(self):
        """test issues with API endpoint"""

        status = READY
        message = "Errors in EBI API endpoints. Please try again later"

        self.common_check(
            status,
            message)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Temporary error in biosample submission 1",
            email.subject)

    def test_token_expired(self):
        """test a token expired during submission"""

        status = READY
        message = (
            "Your token is expired: please submit again to resume "
            "submission")

        self.common_check(
            status,
            message)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Temporary error in biosample submission 1",
            email.subject)

    def test_unmanaged_exception(self):
        """test an unmanaged exception"""

        status = ERROR
        message = "Exception: Unmanaged"

        self.common_check(
            status,
            message)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission 1",
            email.subject)

    def test_error_has_higher_priority(self):
        # update an object with a ready status
        usi_submission = USISubmission.objects.get(pk=2)
        usi_submission.status = READY
        usi_submission.message = "a message"
        usi_submission.save()

        # then raise a generi error
        status = ERROR
        message = "Exception: Unmanaged"

        self.common_check(
            status,
            message)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission 1",
            email.subject)
