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

    # TODO: patch the proper function
    @patch("cryoweb.tasks.time.sleep")
    def test_import_from_cryoweb(self, my_sleep):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = cryoweb.tasks.import_from_cryoweb(submission_id=1)

        # assert a success with data uploading
        self.assertEqual(res, "success")

    # Test a non blocking instance
    @patch("redis.lock.LuaLock.acquire", return_value=False)
    # TODO: patch the proper function
    @patch("cryoweb.tasks.time.sleep")
    def test_import_from_cryoweb_nb(self, my_sleep, my_lock):
        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = cryoweb.tasks.import_from_cryoweb(
            submission_id=1, blocking=False)

        # assert a None value if database is locked
        self.assertIsNone(res)

    # HINT: Uploading the same submission fails or overwrite?
