#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 10:58:42 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from common.constants import ERROR, LOADED
from common.tests import WebSocketMixin
from image_app.models import (
    Submission, Animal, Sample, db_has_data)

from ..helpers import upload_template
from .common import BaseExcelMixin


class ExcelMixin(WebSocketMixin, BaseExcelMixin):
    """Common tests for Excel classes"""

    def test_upload_template(self):
        """Testing uploading and importing data from excel template to UID"""

        # assert upload
        self.assertTrue(upload_template(self.submission))

        # reload submission
        self.submission.refresh_from_db()

        # assert submission messages
        self.assertEqual(
            self.submission.status,
            LOADED)

        self.assertIn(
            "CRBAnim import completed for submission",
            self.submission.message)

        # assert data into database
        self.assertTrue(db_has_data())
        self.assertTrue(Animal.objects.exists())
        self.assertTrue(Sample.objects.exists())

        # check async message called
        message = 'Loaded'
        notification_message = (
            'Template import completed for submission: 1')
        validation_message = {
            'animals': 1, 'samples': 2,
            'animal_unkn': 1, 'sample_unkn': 2,
            'animal_issues': 0, 'sample_issues': 0}

        self.check_message(message, notification_message, validation_message)

    def check_errors(self, my_check, message, notification_message):
        """Common stuff for error in excel template loading"""

        self.assertFalse(upload_template(self.submission))

        # reload submission
        self.submission.refresh_from_db()

        # test my mock method called
        self.assertTrue(my_check.called)

        # reload submission
        self.submission = Submission.objects.get(pk=1)

        self.assertEqual(
            self.submission.status,
            ERROR)

        # check for two distinct messages
        self.assertIn(
            message,
            self.submission.message)

        self.assertNotIn(
            "Template import completed for submission",
            self.submission.message)

        # assert data into database
        self.assertFalse(db_has_data())
        self.assertFalse(Animal.objects.exists())
        self.assertFalse(Sample.objects.exists())

        # check async message called
        self.check_message('Error', notification_message)


class UploadTemplateTestCase(ExcelMixin, TestCase):
    """Test uploading data for Template excel path"""

    pass
