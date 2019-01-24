#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:21 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch, Mock

from django.test import TestCase

from common.tests import PersonMixinTestCase
from image_app.models import Submission, STATUSES, Person, Name

from ..tasks import ValidateTask

# get available statuses
WAITING = STATUSES.get_value('waiting')
LOADED = STATUSES.get_value('loaded')
ERROR = STATUSES.get_value('error')
READY = STATUSES.get_value('ready')
NEED_REVISION = STATUSES.get_value('need_revision')
SUBMITTED = STATUSES.get_value('submitted')


class ValidateSubmissionTest(PersonMixinTestCase, TestCase):
    # an attribute for PersonMixinTestCase
    person = Person

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission",
        "image_app/dictsex",
        "image_app/dictspecie",
        "image_app/dictbreed",
        "image_app/name",
        "image_app/animal",
        "image_app/sample",
        "image_app/ontology"
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

    @patch("validation.tasks.validation.check_with_ruleset")
    @patch("validation.tasks.validation.check_usi_structure")
    def test_validate_submission(self, check_usi, check_ruleset):
        # setting a return value for check_with_ruleset
        validation_result = Mock()
        validation_result.get_overall_status.return_value = "Pass"
        check_ruleset.return_value = [validation_result]

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

        # TODO: test for model message (no messages)

        # assert validation functions called
        self.assertTrue(check_usi.called)
        self.assertTrue(check_ruleset.called)

    @patch("validation.tasks.validation.check_with_ruleset")
    @patch("validation.tasks.validation.check_usi_structure")
    def test_validate_submission_wrong_json(self, check_usi, check_ruleset):
        # setting a return value for check_with_ruleset
        rule_result = Mock()
        rule_result.get_overall_status.return_value = "Pass"
        check_ruleset.return_value = [rule_result]

        # assign a fake response for check_usi_structure
        usi_result = [
            ('Wrong JSON structure: no title field for record with '
             'alias as animal_1'),
            ('Wrong JSON structure: the values for attribute Person '
             'role needs to be in an array for record animal_1')
        ]
        check_usi.return_value = usi_result

        # call task
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with validation taks
        self.assertEqual(res, "success")

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, ERROR)
        self.assertIn(
            "Wrong JSON structure",
            self.submission.message)

        # test for model status. Is the name object
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.status, ERROR)

        self.sample.refresh_from_db()
        self.assertEqual(self.sample.status, ERROR)

        # TODO: test for model message (usi_results)

        # if JSON is not valid, I don't check for ruleset
        self.assertTrue(check_usi.called)
        self.assertFalse(check_ruleset.called)
