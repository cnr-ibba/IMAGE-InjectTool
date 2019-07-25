#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:21 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import json

from collections import Counter
from unittest.mock import patch, Mock
from billiard.einfo import ExceptionInfo
from celery.exceptions import Retry
from pytest import raises
from image_validation.ValidationResult import (
    ValidationResultColumn, ValidationResultRecord)

from django.core import mail
from django.test import TestCase

from common.constants import LOADED, ERROR, READY, NEED_REVISION, COMPLETED
from common.tests import WebSocketMixin
from common.tests import PersonMixinTestCase
from image_app.models import Submission, Person, Name, Animal, Sample

from ..tasks import ValidateTask, ValidationError, ValidateSubmission
from ..helpers import OntologyCacheError, RulesetError
from ..models import ValidationSummary
from .common import PickableMock, MetaDataValidationTestMixin


class ValidateSubmissionMixin(
        PersonMixinTestCase, MetaDataValidationTestMixin):
    """A mixin to define common stuff for testing data validation"""

    # an attribute for PersonMixinTestCase
    person = Person

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
        'image_app/ontology',
        'image_app/organization',
        'image_app/publication',
        'image_app/sample',
        'image_app/submission',
        'image_app/user',
        "validation/validationresult",
        'validation/validationsummary'
    ]

    def setUp(self):
        # calling base methods
        super().setUp()

        # get a submission object
        self.submission = Submission.objects.get(pk=1)

        # set a status which I can validate
        self.submission.status = LOADED
        self.submission.save()

        # track submission ID
        self.submission_id = self.submission.id

        # track names
        self.name_qs = Name.objects.exclude(
            name__contains="unknown").order_by("animal", "id")

        # track animal and samples
        self.animal_qs = Animal.objects.filter(
            name__submission=self.submission)
        self.sample_qs = Sample.objects.filter(
            name__submission=self.submission)

        # track animal and samples count
        self.n_animals = self.animal_qs.count()
        self.n_samples = self.sample_qs.count()

        # setting tasks
        self.my_task = ValidateTask()


class CustomWebSocketMixin(WebSocketMixin):
    """Override setUp to mock websocket objects"""

    def check_message(
            self, message, notification_message, validation_message=None,
            pk=1):

        """Check django channels async messages called"""

        # defining default validation message.
        if not validation_message:
            animal_qs = Animal.objects.filter(
                name__submission=self.submission)
            sample_qs = Sample.objects.filter(
                name__submission=self.submission)

            validation_message = {
                'animals': self.n_animals,
                'samples': self.n_samples,
                'animal_unkn': animal_qs.filter(
                    name__validationresult__isnull=True).count(),
                'sample_unkn': sample_qs.filter(
                    name__validationresult__isnull=True).count(),
                'animal_issues': 0,
                'sample_issues': 0
            }

        self.assertEqual(self.asyncio_mock.call_count, 1)
        self.assertEqual(self.run_until.run_until_complete.call_count, 1)
        self.assertEqual(self.send_msg_ws.call_count, 1)
        self.send_msg_ws.assert_called_with(
            {'message': message,
             'notification_message': notification_message,
             'validation_message': validation_message}, pk)


class ValidateSubmissionTest(ValidateSubmissionMixin, TestCase):

    def setUp(self):
        # calling base methods
        super().setUp()

        # get a submission data object (with no ruleset)
        self.submission_data = ValidateSubmission(
            self.submission, ruleset=None)

    def test_check_valid_statuses(self):
        """test validation supporting statuses"""

        self.assertTrue(self.submission_data.check_valid_statuses())

        # set a fake status
        self.submission_data.animals_statuses['foo'] = 1
        self.assertFalse(self.submission_data.check_valid_statuses())

        # reset and set sample status status
        self.submission_data.animals_statuses = Counter()
        self.submission_data.samples_statuses['foo'] = 1
        self.assertFalse(self.submission_data.check_valid_statuses())

    def test_has_keys(self):
        """Test has error or warning in validation tests"""

        self.assertFalse(self.submission_data.has_errors_in_rules())
        self.assertFalse(self.submission_data.has_warnings_in_rules())

        # set a fake status
        self.submission_data.animals_statuses['Error'] = 1
        self.submission_data.samples_statuses['Warning'] = 1

        self.assertTrue(self.submission_data.has_errors_in_rules())
        self.assertTrue(self.submission_data.has_warnings_in_rules())

    def test_create_validation_summary(self):
        """Create and set validation summary object"""

        # get valdiationsummary objects
        summary_qs = ValidationSummary.objects.filter(
            submission=self.submission)

        # wipe out validationsummary objects
        summary_qs.delete()

        # set up messages
        self.submission_data.animals_statuses['Error'] = 1
        self.submission_data.samples_statuses['Warning'] = 1

        self.submission_data.animals_messages['test error'] = 1
        self.submission_data.samples_messages['test warning'] = 1

        # call function
        self.submission_data.create_validation_summary()

        # assert I have two objects
        self.assertTrue(summary_qs.count(), 2)

        # get animal vs
        animal_summary = summary_qs.get(type="animal")
        self.assertEqual(animal_summary.all_count, self.n_animals)

        sample_summary = summary_qs.get(type="sample")
        self.assertEqual(sample_summary.all_count, self.n_samples)


class ValidateTaskTest(
        CustomWebSocketMixin, ValidateSubmissionMixin, TestCase):

    def setUp(self):
        # calling base methods
        super().setUp()

        # mocking task retry
        self.validate_retry_patcher = patch(
            "validation.tasks.ValidateTask.retry")
        self.validate_retry = self.validate_retry_patcher.start()

    def tearDown(self):
        # stopping my mock objects
        self.validate_retry_patcher.stop()

        # calling base methods
        super().tearDown()

    def test_on_failure(self):
        """Testing on failure methods"""

        exc = Exception("Test")
        task_id = "test_task_id"
        args = [self.submission_id]
        kwargs = {}
        einfo = ExceptionInfo

        # call on_failure method
        self.my_task.on_failure(exc, task_id, args, kwargs, einfo)

        # check submission status and message
        submission = Submission.objects.get(pk=self.submission_id)

        # check submission.state changed
        self.assertEqual(submission.status, ERROR)
        self.assertEqual(
            submission.message,
            "Unknown error in validation - Test")

        # test email sent
        self.assertGreater(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in IMAGE Validation: Unknown error in validation - Test",
            email.subject)

        self.check_message(
            'Error',
            'Unknown error in validation - Test')

    @patch("validation.tasks.ValidateSubmission.validate_model")
    def test_validate_retry(self, my_validate):
        """Test validation with retry"""

        # Set a side effect on the patched methods
        # so that they raise the errors we want.
        self.validate_retry.side_effect = Retry()

        my_validate.side_effect = Exception()

        with raises(Retry):
            self.my_task.run(submission_id=self.submission_id)

        # asserting mock validate_model called
        self.assertTrue(my_validate.called)

        # asserting my mock objects
        self.assertTrue(self.read_in_ruleset.called)
        self.assertTrue(self.check_ruleset.called)
        self.assertTrue(self.validate_retry.called)

        # asserting django channels not called
        self.check_message_not_called()

    @patch("validation.tasks.ValidateSubmission.validate_model")
    def test_issues_with_api(self, my_validate):
        """Test errors with validation API"""

        my_validate.side_effect = json.decoder.JSONDecodeError(
            msg="test", doc="test", pos=1)

        # call task. No retries with issues at EBI
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # this is the message I want
        message = "Errors in EBI API endpoints. Please try again later"

        # check submission.status changed to NEED_REVISION
        self.assertEqual(self.submission.status, LOADED)
        self.assertIn(
            message,
            self.submission.message)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in IMAGE Validation: %s" % message,
            email.subject)

        # asserting mock validate_model called
        self.assertTrue(my_validate.called)

        # asserting my mock objects
        self.assertTrue(self.read_in_ruleset.called)
        self.assertTrue(self.check_ruleset.called)
        self.assertFalse(self.validate_retry.called)

        self.check_message(
            'Loaded',
            'Errors in EBI API endpoints. Please try again later'
        )

    def test_issues_with_ontologychache(self):
        """Test errors with validation API when loading OntologyCache
        objects"""

        # return a custom exception with read_in_ruleset
        self.read_in_ruleset.side_effect = OntologyCacheError("test exception")

        # call task. No retries with issues at EBI
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # this is the message I want
        message = "Errors in EBI API endpoints. Please try again later"

        # check submission.status changed to LOADED
        self.assertEqual(self.submission.status, LOADED)
        self.assertIn(
            message,
            self.submission.message)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in IMAGE Validation: %s" % message,
            email.subject)

        # asserting my mock objects
        self.assertTrue(self.read_in_ruleset.called)
        self.assertFalse(self.check_ruleset.called)
        self.assertFalse(self.validate_retry.called)

        self.check_message(
            'Loaded',
            'Errors in EBI API endpoints. Please try again later')

    def test_issues_with_ruleset(self):
        """Test errors with ruleset"""

        # return a custom exception with read_in_ruleset
        self.read_in_ruleset.side_effect = RulesetError(["test exception"])

        # call task. No retries with issues at EBI
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # this is the message I want
        message = (
            "Error in IMAGE-metadata ruleset. Please inform InjectTool team")

        # check submission.status changed to ERROR
        self.assertEqual(self.submission.status, ERROR)
        self.assertIn(
            message,
            self.submission.message)

        # test email sent
        self.assertGreater(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in IMAGE Validation: %s" % message,
            email.subject)

        # asserting my mock objects
        self.assertTrue(self.read_in_ruleset.called)
        self.assertFalse(self.check_ruleset.called)
        self.assertFalse(self.validate_retry.called)

        self.check_message(
            'Error',
            'Error in IMAGE-metadata ruleset. Please inform InjectTool team')

    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    def test_validate_submission(
            self, my_validate, my_check):
        """Test a valid submission. Simulate image_validation result and
        status changes"""

        # setting check_usi_structure result. now is a ValidateResultRecord
        result = PickableMock()
        result.get_overall_status.return_value = "Pass"
        result.get_messages.return_value = []
        my_check.return_value = result

        # setting a return value for check_with_ruleset
        validation_result = Mock()
        validation_result.get_overall_status.return_value = "Pass"
        validation_result.get_messages.return_value = ["A message"]
        result_set = Mock()
        result_set.get_comparable_str.return_value = "A message"
        validation_result.result_set = [result_set]
        my_validate.return_value = validation_result

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, READY)
        self.assertEqual(
            self.submission.message,
            "Submission validated with success")

        # check Names (they are all ok)
        for name in self.name_qs:
            self.assertEqual(name.status, READY)

            # test for model message (usi_results)
            self.assertEqual(
                name.validationresult.messages, ["A message"])
            self.assertEqual(name.validationresult.status, "Pass")

        # assert validation functions called
        self.assertTrue(my_check.called)
        self.assertTrue(my_validate.called)

        # asserting my mock objects
        self.assertTrue(self.read_in_ruleset.called)
        self.assertTrue(self.check_ruleset.called)
        self.assertFalse(self.validate_retry.called)

        # no unknown and sample with issues
        validation_message = {
            'animals': self.n_animals,
            'samples': self.n_samples,
            'animal_unkn': 0, 'sample_unkn': 0,
            'animal_issues': 0, 'sample_issues': 0}

        self.check_message(
            'Ready',
            'Submission validated with success',
            validation_message=validation_message
        )

    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    def test_validate_submission_wrong_json(
            self, my_validate, my_check):
        """Test an error in JSON format"""

        # setting check_usi_structure result. now is a ValidateResultRecord
        messages = [
            ('Wrong JSON structure: no title field for record with '
             'alias as animal_1'),
            ('Wrong JSON structure: the values for attribute Person '
             'role needs to be in an array for record animal_1')
        ]

        usi_result = ValidationResultRecord("animal_1")
        usi_result.add_validation_result_column(
            ValidationResultColumn(
                "error",
                messages[0],
                "animal_1",
                "")
        )
        usi_result.add_validation_result_column(
            ValidationResultColumn(
                "error",
                messages[1],
                "animal_1",
                "")
        )

        my_check.return_value = usi_result

        # setting a return value for check_with_ruleset
        rule_result = Mock()
        rule_result.get_overall_status.return_value = "Pass"
        my_validate.return_value = rule_result

        # call task
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, NEED_REVISION)
        self.assertIn(
            "Validation got errors",
            self.submission.message)

        # check Names (they require revisions)
        for name in self.name_qs:
            self.assertEqual(name.status, NEED_REVISION)

            # test for model message (usi_results)
            self.assertEqual(
                name.validationresult.messages, usi_result.get_messages())
            self.assertEqual(
                name.validationresult.status, usi_result.get_overall_status())

        # if JSON is not valid, I don't check for ruleset
        self.assertTrue(my_check.called)
        self.assertFalse(my_validate.called)

        # asserting my mock objects
        self.assertTrue(self.read_in_ruleset.called)
        self.assertTrue(self.check_ruleset.called)
        self.assertFalse(self.validate_retry.called)

        # all sample and animals have issues
        self.check_message(
            'Need Revision',
            ('Validation got errors: Error in metadata. '
             'Need revisions before submit'),
            {'animals': self.n_animals, 'samples': self.n_samples,
             'animal_unkn': 0, 'sample_unkn': 0,
             'animal_issues': self.n_animals,
             'sample_issues': self.n_samples},
            1)

    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    def test_unsupported_status(
            self, my_validate, my_check):
        """This test will ensure that image_validation ValidationResultRecord
        still support the same statuses"""

        # setting check_usi_structure result. now is a ValidateResultRecord
        result = PickableMock()
        result.get_overall_status.return_value = "Pass"
        result.get_messages.return_value = []
        my_check.return_value = result

        # setting a return value for check_with_ruleset
        rule_result = PickableMock()
        rule_result.get_overall_status.return_value = "A fake status"
        rule_result.get_messages.return_value = ["A fake message", ]

        result_set = Mock()
        result_set.get_comparable_str.return_value = "A fake message"
        rule_result.result_set = [result_set]

        my_validate.return_value = rule_result

        # call task
        self.assertRaisesRegex(
            ValidationError,
            "Unsupported validation status for submission",
            self.my_task.run,
            submission_id=self.submission_id)

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, ERROR)
        self.assertIn(
            "Unsupported validation status for submission",
            self.submission.message)

        # if JSON is not valid, I don't check for ruleset
        self.assertTrue(my_check.called)
        self.assertTrue(my_validate.called)

        # asserting my mock objects
        self.assertTrue(self.read_in_ruleset.called)
        self.assertTrue(self.check_ruleset.called)
        self.assertFalse(self.validate_retry.called)

        self.check_message(
            message='Error',
            notification_message=(
                "Validation got errors: Unsupported validation status "
                "for submission Cryoweb (United Kingdom, test)"),
            validation_message={
                'animals': self.n_animals, 'samples': self.n_samples,
                'animal_unkn': 0, 'sample_unkn': 0,
                'animal_issues': self.n_animals,
                'sample_issues': self.n_samples},
            pk=1)

    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    def test_validate_submission_warnings(
            self, my_validate, my_check):
        """A submission with warnings is a READY submission"""

        # setting check_usi_structure result. now is a ValidateResultRecord
        result = PickableMock()
        result.get_overall_status.return_value = "Pass"
        result.get_messages.return_value = []
        my_check.return_value = result

        # setting a return value for check_with_ruleset
        result1 = ValidationResultRecord("animal_1")
        result1.add_validation_result_column(
            ValidationResultColumn(
                "warning",
                "warn message",
                "animal_1",
                "warn column")
        )

        result2 = ValidationResultRecord("animal_2")
        result2.add_validation_result_column(
            ValidationResultColumn(
                "pass",
                "a message",
                "animal_2",
                "")
        )

        result3 = ValidationResultRecord("animal_3")
        result3.add_validation_result_column(
            ValidationResultColumn(
                "pass",
                "a message",
                "animal_3",
                "")
        )

        result4 = ValidationResultRecord("sample_1")
        result4.add_validation_result_column(
            ValidationResultColumn(
                "pass",
                "a message",
                "sample_1",
                "")
        )

        # add results to result set
        responses = [result1, result2, result3, result4]
        my_validate.side_effect = responses

        # call task
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, READY)
        self.assertIn(
            "Submission validated with some warnings",
            self.submission.message)

        # check Names (they are all ok)
        for i, name in enumerate(self.name_qs):
            # get the appropriate ValidationResultRecord
            result = responses[i]

            # all objects are ready for submissions
            self.assertEqual(name.status, READY)

            self.assertEqual(
                name.validationresult.messages,
                result.get_messages())

            self.assertEqual(
                name.validationresult.status,
                result.get_overall_status())

        # test for my methods called
        self.assertTrue(my_check.called)
        self.assertTrue(my_validate.called)

        # asserting my mock objects
        self.assertTrue(self.read_in_ruleset.called)
        self.assertTrue(self.check_ruleset.called)
        self.assertFalse(self.validate_retry.called)

        self.check_message(
            message='Ready',
            notification_message='Submission validated with some warnings',
            validation_message={
                'animals': self.n_animals, 'samples': self.n_samples,
                'animal_unkn': 0, 'sample_unkn': 0,
                'animal_issues': 0, 'sample_issues': 0},
            pk=1)

    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    def test_validate_submission_errors(
            self, my_validate, my_check):
        """A submission with errors is a NEED_REVISION submission"""

        # setting check_usi_structure result. now is a ValidateResultRecord
        result = PickableMock()
        result.get_overall_status.return_value = "Pass"
        result.get_messages.return_value = []
        my_check.return_value = result

        # setting a return value for check_with_ruleset
        result1 = ValidationResultRecord("animal_1")
        result1.add_validation_result_column(
            ValidationResultColumn(
                "warning",
                "warn message",
                "animal_1",
                "warn column")
        )

        result2 = ValidationResultRecord("animal_2")
        result2.add_validation_result_column(
            ValidationResultColumn(
                "pass",
                "a message",
                "animal_2",
                "")
        )

        result3 = ValidationResultRecord("animal_3")
        result3.add_validation_result_column(
            ValidationResultColumn(
                "pass",
                "a message",
                "animal_3",
                "")
        )

        result4 = ValidationResultRecord("sample_1")
        result4.add_validation_result_column(
            ValidationResultColumn(
                "error",
                "error message",
                "sample_1",
                "error column")
        )

        # add results to result set
        responses = [result1, result2, result3, result4]
        my_validate.side_effect = responses

        # call task
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, NEED_REVISION)
        self.assertIn(
            "Error in metadata",
            self.submission.message)

        # check Names (they are all ok, except 1 - sample)
        for i, name in enumerate(self.name_qs):
            # get the appropriate ValidationResultRecord
            result = responses[i]

            if hasattr(name, "animal"):
                self.assertEqual(name.status, READY)

            else:
                # sample has errors
                self.assertEqual(name.status, NEED_REVISION)

            self.assertEqual(
                name.validationresult.messages,
                result.get_messages())

            self.assertEqual(
                name.validationresult.status,
                result.get_overall_status())

        # test for my methods called
        self.assertTrue(my_check.called)
        self.assertTrue(my_validate.called)

        # asserting my mock objects
        self.assertTrue(self.read_in_ruleset.called)
        self.assertTrue(self.check_ruleset.called)
        self.assertFalse(self.validate_retry.called)

        self.check_message(
            message='Need Revision',
            notification_message=(
                'Validation got errors: Error in '
                'metadata. Need revisions before submit'),
            validation_message={
                'animals': self.n_animals, 'samples': self.n_samples,
                'animal_unkn': 0, 'sample_unkn': 0,
                'animal_issues': 0, 'sample_issues': 1},
            pk=1)


class ValidateSubmissionStatusTest(ValidateSubmissionMixin, TestCase):
    """Check database statuses after calling validation"""

    def setUp(self):
        # calling base setup
        super().setUp()

        # get a submission data object (with no ruleset)
        self.submission_data = ValidateSubmission(
            self.submission, ruleset=None)

        # track an animal for testing
        self.animal = Animal.objects.get(pk=1)
        self.animal_name = self.animal.name

    def check_status(self, status, messages, name_status):
        """Test if I can update status for a model that pass validation"""

        result = PickableMock()
        result.get_overall_status.return_value = status
        result.get_messages.return_value = messages
        result_set = Mock()
        result_set.get_comparable_str.return_value = "A message"
        result.result_set = [result_set]

        submission_statuses = Counter(
            {'Pass': 0,
             'Warning': 0,
             'Error': 0,
             'JSON': 0})

        # calling update statuses
        self.submission_data.update_statuses(
            submission_statuses, self.animal, result)

        # Test for animal status
        self.animal_name.refresh_from_db()
        self.assertEqual(self.animal_name.status, name_status)

        # get validation result object
        validationresult = self.animal_name.validationresult
        self.assertEqual(validationresult.status, status)
        self.assertEqual(validationresult.messages, messages)

        # test submission status
        self.assertEqual(submission_statuses[status], 1)

    def test_update_status_pass(self):
        status = 'Pass'
        messages = ['Passed all tests']
        name_status = READY

        self.check_status(status, messages, name_status)

    def test_update_status_warning(self):
        status = 'Warning'
        messages = ['issued a warning']
        name_status = READY

        self.check_status(status, messages, name_status)

    def test_update_status_error(self):
        status = 'Error'
        messages = ['issued an error']
        name_status = NEED_REVISION

        self.check_status(status, messages, name_status)


class ValidateUpdatedSubmissionStatusTest(ValidateSubmissionMixin, TestCase):
    """Check database statuses after calling validation for an updated
    submission (a submission completed and submitted to biosample in which
    I want to modify a thing)"""

    def setUp(self):
        # call base method
        super().setUp()

        # get a submission data object (with no ruleset)
        self.submission_data = ValidateSubmission(
            self.submission, ruleset=None)

        # take all names and set them to completed, as after a successful
        # submission:
        self.name_qs.update(status=COMPLETED)

        # take the animal name I want to update
        self.animal_name = Name.objects.get(pk=3)

        # update submission status. Simulate a completed submission in which
        # I want to update something
        self.submission.status = NEED_REVISION
        self.submission.save()

        # update name objects. In this case, animal was modified
        self.animal_name.status = NEED_REVISION
        self.animal_name.save()

    def update_status(self, status, messages, name_status):
        """Test if I can update status for a model that pass validation"""

        # modelling validation same result for every object
        result = PickableMock()
        result.get_overall_status.return_value = status
        result.get_messages.return_value = messages

        result_set = Mock()
        result_set.get_comparable_str.return_value = "A message"
        result.result_set = [result_set]

        submission_statuses = Counter(
            {'Pass': 0,
             'Warning': 0,
             'Error': 0,
             'JSON': 0})

        # calling update statuses on name objects
        for name in self.name_qs:
            if hasattr(name, "animal"):
                self.submission_data.update_statuses(
                    submission_statuses,
                    name.animal,
                    result)
            else:
                self.submission_data.update_statuses(
                    submission_statuses,
                    name.sample,
                    result)

        # refreshing data from db
        self.animal_name.refresh_from_db()

    def test_update_status_pass(self):
        status = 'Pass'
        messages = ['Passed all tests']
        name_status = READY

        self.update_status(status, messages, name_status)

        # asserting status change for animal
        self.assertEqual(self.animal_name.status, name_status)

        # validationresult is tested outside this class

        # other statuses are unchanged
        for name in self.name_qs.exclude(pk=self.animal_name.pk):
            self.assertEqual(name.status, COMPLETED)

    def test_update_status_warning(self):
        status = 'Warning'
        messages = ['issued a warning']
        name_status = READY

        self.update_status(status, messages, name_status)

        # asserting status change for animal
        self.assertEqual(self.animal_name.status, name_status)

        # other statuses are unchanged
        for name in self.name_qs.exclude(pk=self.animal_name.pk):
            self.assertEqual(name.status, COMPLETED)

    def test_update_status_error(self):
        status = 'Error'
        messages = ['issued an error']
        name_status = NEED_REVISION

        self.update_status(status, messages, name_status)

        # all statuses are changed (and need revisions)
        for name in self.name_qs:
            self.assertEqual(name.status, NEED_REVISION)
