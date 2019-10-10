#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 12:37:21 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase


from ..tasks import clearsessions


class TestClearSession(TestCase):
    @patch('django.core.management.call_command')
    def test_clearsession(self, my_patch):
        result = clearsessions.run()

        self.assertEqual(result, "Session cleaned with success")
        self.assertTrue(my_patch.called)
