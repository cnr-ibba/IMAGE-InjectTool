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

from common.constants import LOADED, ERROR, READY, NEED_REVISION
from common.tests import PersonMixinTestCase
from image_app.models import Submission, Person, Name

from ..tasks import ValidateTask, ValidationError


# https://github.com/testing-cabal/mock/issues/139#issuecomment-122128815
class PickableMock(Mock):
    """Provide a __reduce__ method to allow pickling mock objects"""

    def __reduce__(self):
        return (Mock, ())


class ValidateSubmissionTest(PersonMixinTestCase, TestCase):
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
        "validation/validationresult"
    ]

    def setUp(self):
        # get a submission object
        self.submission = Submission.objects.get(pk=1)

        # set a status which I can validate
        self.submission.status = LOADED
        self.submission.save()

        # track submission ID
        self.submission_id = self.submission.id

        # track animal and sample. Track Name objects
        self.animal = Name.objects.get(pk=3)
        self.sample = Name.objects.get(pk=4)

        # setting tasks
        self.my_task = ValidateTask()

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
            "Error in IMAGE Validation: Test")

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in IMAGE Validation: %s" % self.submission_id,
            email.subject)

    @patch("validation.tasks.MetaDataValidation.read_in_ruleset")
    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    @patch("validation.tasks.ValidateTask.retry")
    def test_validate_retry(self, my_retry, my_validate, my_check, my_read):
        """Test validation with retry"""

        # setting check_usi_structure result
        my_check.return_value = []

        # Set a side effect on the patched methods
        # so that they raise the errors we want.
        my_retry.side_effect = Retry()
        my_validate.side_effect = Exception()

        with raises(Retry):
            self.my_task.run(submission_id=self.submission_id)

        self.assertTrue(my_validate.called)
        self.assertTrue(my_retry.called)
        self.assertTrue(my_check.called)
        self.assertTrue(my_read.called)

    @patch("validation.tasks.MetaDataValidation.read_in_ruleset")
    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    @patch("validation.tasks.ValidateTask.retry")
    def test_issues_with_api(self, my_retry, my_validate, my_check, my_read):
        """Test errors with validation API"""

        # Set a side effect on the patched methods
        # so that they raise the errors we want.
        my_retry.side_effect = Retry()
        my_check.return_value = []
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

        self.assertTrue(my_validate.called)
        self.assertFalse(my_retry.called)
        self.assertTrue(my_check.called)
        self.assertTrue(my_read.called)

    @patch("validation.tasks.MetaDataValidation.read_in_ruleset")
    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    def test_validate_submission(self, my_validate, my_check, my_read):
        # setting check_usi_structure result
        my_check.return_value = []

        # setting a return value for check_with_ruleset
        validation_result = Mock()
        validation_result.get_overall_status.return_value = "Pass"
        validation_result.get_messages.return_value = ["A message"]
        my_validate.return_value = [validation_result]

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

        # test for model status. Is the name object
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.status, READY)

        self.sample.refresh_from_db()
        self.assertEqual(self.sample.status, READY)

        # test for model message (usi_results)
        self.assertEqual(self.animal.validationresult.messages, ["A message"])
        self.assertEqual(self.animal.validationresult.status, "Pass")

        self.assertEqual(self.sample.validationresult.messages, ["A message"])
        self.assertEqual(self.sample.validationresult.status, "Pass")

        # assert validation functions called
        self.assertTrue(my_check.called)
        self.assertTrue(my_validate.called)
        self.assertTrue(my_read.called)

    @patch("validation.tasks.MetaDataValidation.read_in_ruleset")
    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    def test_validate_submission_wrong_json(
            self, my_validate, my_check, my_read):

        # assign a fake response for check_usi_structure
        usi_result = [
            ('Wrong JSON structure: no title field for record with '
             'alias as animal_1'),
            ('Wrong JSON structure: the values for attribute Person '
             'role needs to be in an array for record animal_1')
        ]
        my_check.return_value = usi_result

        # setting a return value for check_with_ruleset
        rule_result = Mock()
        rule_result.get_overall_status.return_value = "Pass"
        my_validate.return_value = [rule_result]

        # call task
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, NEED_REVISION)
        self.assertIn(
            "Wrong JSON structure",
            self.submission.message)

        # test for model status. Is the name object
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.status, NEED_REVISION)

        self.sample.refresh_from_db()
        self.assertEqual(self.sample.status, NEED_REVISION)

        # test for model message (usi_results)
        self.assertEqual(self.animal.validationresult.messages, usi_result)
        self.assertEqual(
            self.animal.validationresult.status, "Wrong JSON structure")

        self.assertEqual(self.sample.validationresult.messages, usi_result)
        self.assertEqual(
            self.sample.validationresult.status, "Wrong JSON structure")

        # if JSON is not valid, I don't check for ruleset
        self.assertTrue(my_check.called)
        self.assertFalse(my_validate.called)
        self.assertTrue(my_read.called)

    @patch("validation.tasks.MetaDataValidation.read_in_ruleset")
    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    def test_unsupported_status(self, my_validate, my_check, my_read):
        # setting check_usi_structure result
        my_check.return_value = []

        # setting a return value for check_with_ruleset
        rule_result = PickableMock()
        rule_result.get_overall_status.return_value = "A fake status"
        rule_result.get_messages.return_value = ["A fake message", ]
        my_validate.return_value = [rule_result]

        # call task
        self.assertRaisesRegex(
            ValidationError,
            "Error in statuses for submission",
            self.my_task.run,
            submission_id=self.submission_id)

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, ERROR)
        self.assertIn(
            "Error in statuses for submission",
            self.submission.message)

        # if JSON is not valid, I don't check for ruleset
        self.assertTrue(my_check.called)
        self.assertTrue(my_validate.called)
        self.assertTrue(my_read.called)

    @patch("validation.tasks.MetaDataValidation.read_in_ruleset")
    @patch("validation.tasks.MetaDataValidation.check_usi_structure")
    @patch("validation.tasks.MetaDataValidation.validate")
    def test_validate_submission_errors(
            self, my_validate, my_check, my_read):

        # setting check_usi_structure result
        my_check.return_value = []

        # setting a return value for check_with_ruleset
        result1 = ValidationResultRecord("animal_1")
        result1.add_validation_result_column(
            ValidationResultColumn("warning", "warn message", "animal_1")
        )

        result2 = ValidationResultRecord("sample_1")
        result2.add_validation_result_column(
            ValidationResultColumn("error", "error message", "sample_1")
        )

        # add results to result set
        my_validate.side_effect = [[result1], [result2]]

        # call task
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, NEED_REVISION)
        self.assertIn(
            "Error in metadata rules",
            self.submission.message)

        # test for model status. Is the name object
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.status, NEED_REVISION)

        self.sample.refresh_from_db()
        self.assertEqual(self.sample.status, NEED_REVISION)

        # test for model message (usi_results)
        test = self.animal.validationresult
        self.assertEqual(test.messages, result1.get_messages())
        self.assertEqual(test.status, "Warning")

        test = self.sample.validationresult
        self.assertEqual(test.messages, result2.get_messages())
        self.assertEqual(test.status, "Error")

        # test for my methods called
        self.assertTrue(my_check.called)
        self.assertTrue(my_validate.called)
        self.assertTrue(my_read.called)

    def test_update_statuses_more_result(self):
        """Test update_statuses with more than one results, or none of them"""

        # testing exceptions
        self.assertRaisesRegex(
            ValidationError,
            "Number of validation results are different from expectations",
            self.my_task.update_statuses,
            Counter(),
            self.animal,
            [Mock(), Mock()])

        self.assertRaisesRegex(
            ValidationError,
            "Number of validation results are different from expectations",
            self.my_task.update_statuses,
            Counter(),
            self.animal,
            [])
