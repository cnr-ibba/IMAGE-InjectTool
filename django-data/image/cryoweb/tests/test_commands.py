#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 25 17:21:14 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Testing management commands (https://stackoverflow.com/a/6513372)

"""

from django.core.management import call_command
from django.test import TestCase


class CommandsTestCase(TestCase):
    databases = {'default', 'cryoweb'}

    def test_truncate_cryoweb(self):
        " Test initializedb command."

        args = []
        opts = {}
        call_command('truncate_cryoweb_tables', *args, **opts)
