#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 13:23:20 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from ..helpers import is_target_in_message


class TargetInMessageTest(TestCase):
    def test_target_in(self):
        test = is_target_in_message('meow', ['meow', 'bark'])
        self.assertTrue(test)

    def test_target_not_in(self):
        test = is_target_in_message('meow', ['bark'])
        self.assertFalse(test)
