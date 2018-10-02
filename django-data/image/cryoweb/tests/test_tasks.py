#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 16:19:19 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase

import cryoweb.tasks
from ..helpers import CryoWebImportError


class ImportCryowebTest(TestCase):
    # import this file and populate database once
    fixtures = [
        "cryoweb/user",
        "cryoweb/dictrole",
        "cryoweb/organization",
        "cryoweb/dictcountry",
        "cryoweb/submission",
        "cryoweb/dictsex",
        "cryoweb/dictspecie",
        "cryoweb/speciesynonim"
    ]

    # patching upload_cryoweb and truncate database
    @patch("cryoweb.tasks.truncate_database")
    @patch("cryoweb.tasks.cryoweb_import")
    @patch("cryoweb.tasks.upload_cryoweb", return_value=True)
    def test_import_from_cryoweb(
            self, my_upload, my_import, my_truncate):
        """Testing cryoweb import"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = cryoweb.tasks.import_from_cryoweb(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert that method were called
        self.assertTrue(my_upload.called)
        self.assertTrue(my_import.called)

        # ensure that database is truncated
        self.assertTrue(my_truncate.called)

    @patch("cryoweb.helpers.cryoweb_has_data", return_value=True)
    @patch("cryoweb.tasks.truncate_database")
    def test_import_has_data(self, my_truncate, my_has_data):
        """Test cryoweb import with data in cryoweb database"""

        # importing data in staged area with data raises an exception
        self.assertRaises(
            CryoWebImportError,
            cryoweb.tasks.import_from_cryoweb,
            submission_id=1)

        self.assertTrue(my_has_data.called)

        # When I got an exception, task escapes without cleaning database
        self.assertFalse(my_truncate.called)

    @patch("cryoweb.tasks.truncate_database")
    @patch("cryoweb.tasks.cryoweb_import")
    @patch("cryoweb.tasks.upload_cryoweb", return_value=False)
    def test_error_in_uploading(
            self, my_upload, my_import, my_truncate):
        """Testing error in importing data into cryoweb"""

        res = cryoweb.tasks.import_from_cryoweb(submission_id=1)

        # assert an error in data uploading
        self.assertEqual(res, "error in uploading cryoweb data")

        # assert that method were called
        self.assertTrue(my_upload.called)
        self.assertFalse(my_import.called)

        # ensure that database is truncated
        self.assertTrue(my_truncate.called)

    @patch("cryoweb.tasks.truncate_database")
    @patch("cryoweb.tasks.cryoweb_import", return_value=False)
    @patch("cryoweb.tasks.upload_cryoweb", return_value=True)
    def test_error_in_uploading2(
            self, my_upload, my_import, my_truncate):
        """Testing error in importing data from cryoweb to UID"""

        res = cryoweb.tasks.import_from_cryoweb(submission_id=1)

        # assert an error in data uploading
        self.assertEqual(res, "error in importing cryoweb data")

        # assert that method were called
        self.assertTrue(my_upload.called)
        self.assertTrue(my_import.called)

        # ensure that database is truncated
        self.assertTrue(my_truncate.called)

    # Test a non blocking instance
    @patch("redis.lock.LuaLock.acquire", return_value=False)
    @patch("cryoweb.helpers.cryoweb_import")
    @patch("cryoweb.helpers.upload_cryoweb", return_value=True)
    @patch("cryoweb.models.db_has_data", return_value=False)
    @patch("cryoweb.models.truncate_database")
    def test_import_from_cryoweb_nb(
            self, my_truncate, my_has_data, my_upload, my_import, my_lock):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = cryoweb.tasks.import_from_cryoweb(
            submission_id=1, blocking=False)

        # assert a None value if database is locked
        self.assertIsNone(res)

        # assert that methods were not called
        self.assertFalse(my_truncate.called)
        self.assertFalse(my_upload.called)
        self.assertFalse(my_import.called)

    # HINT: Uploading the same submission fails or overwrite?
