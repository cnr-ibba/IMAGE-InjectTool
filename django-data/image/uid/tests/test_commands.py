#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 17 17:25:22 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Testing management commands (https://stackoverflow.com/a/6513372)

"""

from django.core.management import call_command
from django.test import TestCase


class CommandsTestCase(TestCase):
    # TODO: need to define a custom settings.py

    def test_initializedb(self):
        " Test initializedb command."

        args = []
        opts = {}
        call_command('initializedb', *args, **opts)

    def test_truncate_uid(self):
        " Test initializedb command."

        args = []
        opts = {}
        call_command('truncate_image_tables', *args, **opts)

    def test_truncate_uid_all(self):
        " Test initializedb command."

        args = ["--all"]
        opts = {}
        call_command('truncate_image_tables', *args, **opts)
