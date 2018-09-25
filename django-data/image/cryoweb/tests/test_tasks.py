#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 16:19:19 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase

import cryoweb.tasks


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
    @patch("cryoweb.tasks.upload_cryoweb", return_value=True)
    @patch("cryoweb.tasks.cryoweb_has_data", return_value=True)
    @patch("cryoweb.tasks.truncate_database")
    def test_import_from_cryoweb(self, my_upload, my_has_data, my_truncate):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = cryoweb.tasks.import_from_cryoweb(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

    # patching an error in uploading cryoweb and truncate database
    @patch("cryoweb.tasks.upload_cryoweb", return_value=False)
    @patch("cryoweb.tasks.truncate_database")
    def test_error_in_uploading_cryoweb_data(self, my_upload, my_truncate):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = cryoweb.tasks.import_from_cryoweb(submission_id=1)

        # assert an error in data uploading
        self.assertEqual(res, "error in uploading cryoweb data")

    # Test a non blocking instance
    @patch("redis.lock.LuaLock.acquire", return_value=False)
    @patch("cryoweb.tasks.upload_cryoweb")
    @patch("cryoweb.tasks.truncate_database")
    def test_import_from_cryoweb_nb(self, my_upload, my_lock, my_truncate):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = cryoweb.tasks.import_from_cryoweb(
            submission_id=1, blocking=False)

        # assert a None value if database is locked
        self.assertIsNone(res)

    # HINT: Uploading the same submission fails or overwrite?
