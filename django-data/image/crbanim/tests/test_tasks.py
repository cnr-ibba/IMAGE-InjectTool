#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:27 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase

from .common import BaseTestCase
from ..tasks import ImportCRBAnimTask


class ImportCRBAnimTaskTest(BaseTestCase, TestCase):
    def setUp(self):
        # calling my base class setup
        super().setUp()

        # setting task
        self.my_task = ImportCRBAnimTask()

    @patch("crbanim.tasks.upload_crbanim", return_value=True)
    def test_import_from_crbanim(self, my_upload):
        """Testing crbanim import"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert that method were called
        self.assertTrue(my_upload.called)

    @patch("crbanim.tasks.upload_crbanim", return_value=False)
    def test_import_from_crbanim_errors(self, my_upload):
        """Testing crbianim import with errors"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "Error in uploading CRBAnim data")

        # assert that method were called
        self.assertTrue(my_upload.called)
