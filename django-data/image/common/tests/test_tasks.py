#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 12:37:21 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase


from ..tasks import clearsessions, ExclusiveTask


class TestClearSession(TestCase):
    @patch('django.core.management.call_command')
    def test_clearsession(self, my_patch):
        result = clearsessions.run()

        self.assertEqual(result, "Session cleaned with success")
        self.assertTrue(my_patch.called)


class ExclusiveTasktest(TestCase):
    def setUp(self):
        self.my_task = ExclusiveTask()
        self.my_task.name = "test"
        self.my_task.lock_id = "test"

    @patch('common.tasks.ExclusiveTask.apply_async', return_value=True)
    def test_delay(self, my_func):
        self.assertTrue(self.my_task.delay())
        self.assertTrue(my_func.called)

    @patch("redis.lock.Lock.acquire", return_value=False)
    @patch('common.tasks.ExclusiveTask.apply_async', return_value=True)
    def test_delay_blocking(self, my_func, my_lock):
        result = self.my_task.delay()
        self.assertEqual("test already running!", result)
        self.assertFalse(my_func.called)
        self.assertTrue(my_lock.called)
