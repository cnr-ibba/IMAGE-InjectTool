#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:21 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase

from common.tests import PersonMixinTestCase
from image_app.models import Submission, STATUSES, Person

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
        submission = Submission.objects.get(pk=1)

        # set a status which I can validate
        submission.status = LOADED
        submission.save()

        # track submission ID
        self.submission_id = submission.id

        # setting tasks
        self.my_task = ValidateTask()

    @patch("validation.tasks.validation.check_with_ruleset")
    @patch("validation.tasks.validation.check_usi_structure")
    def test_validate_submission(self, check_usi, check_ruleset):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=self.submission_id)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # check submission status and message
        submission = Submission.objects.get(pk=1)

        # check submission.state changed
        self.assertEqual(submission.status, READY)
        self.assertEqual(
            submission.message,
            "Submission validated with success")

        self.assertTrue(check_usi.called)
        self.assertTrue(check_ruleset.called)
