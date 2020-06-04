#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 16:19:41 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

from unittest.mock import patch, Mock

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from common.constants import COMPLETED

from ..models import Submission
from ..tasks import CleanUpTask, SearchOrphanTask
from .common import BioSamplesMixin


class CleanUpTaskTestCase(TestCase):

    fixtures = [
        "biosample/submission",
        "uid/dictcountry",
        "uid/dictrole",
        "uid/organization",
        "uid/submission",
        "uid/user",
    ]

    def setUp(self):
        # calling my base setup
        super().setUp()

        # fix status for objects
        Submission.objects.update(status=COMPLETED)

        # get one objcet and updatete time
        Submission.objects.filter(pk=1).update(updated_at=timezone.now())

        # define my task
        self.my_task = CleanUpTask()

        # change lock_id (useful when running test during cron)
        self.my_task.lock_id = "test-CleanUpTask"

    def test_clean_up(self):
        """Test clean_up task"""

        for submission in Submission.objects.all():
            print(submission, submission.updated_at)

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert one object in the database
        self.assertEqual(Submission.objects.count(), 1)

    # Test a non blocking instance
    @patch("redis.lock.Lock.acquire", return_value=False)
    def test_clean_up_nb(self, my_lock):
        """Test CleanUpTask while a lock is present"""

        res = self.my_task.run()

        # assert database is locked
        self.assertEqual(res, "%s already running!" % (self.my_task.name))

        # assert two object in the database (fake running)
        self.assertEqual(Submission.objects.count(), 2)


class SearchOrphanTaskTestCase(TestCase):

    fixtures = [
        'biosample/managedteam',
        'biosample/orphansample',
        'uid/dictspecie',
    ]

    def setUp(self):
        # calling my base setup
        super().setUp()

        # ovveride the base patcher method
        self.asyncio_mock_patcher = patch(
            'asyncio.new_event_loop')
        self.asyncio_mock = self.asyncio_mock_patcher.start()

        # mocking asyncio return value
        self.run_until = self.asyncio_mock.return_value
        self.run_until.run_until_complete = Mock()

        # another patch
        self.check_samples_patcher = patch(
            'biosample.tasks.cleanup.check_samples')
        self.check_samples = self.check_samples_patcher.start()

        # define my task
        self.my_task = SearchOrphanTask()

        # change lock_id (useful when running test during cron)
        self.my_task.lock_id = "test-SearchOrphanTask"

    def tearDown(self):
        # stopping mock objects
        self.asyncio_mock_patcher.stop()
        self.check_samples_patcher.stop()

        # calling base methods
        super().tearDown()

    def test_search_orphan(self):
        """Test SearchOrphanTask task"""

        # NOTE that I'm calling the function directly, without delay
        # (AsyncResult). I've patched the time consuming task
        res = self.my_task.run()

        # assert a success with data uploading
        self.assertEqual(res, "success")

        # assert function called
        self.assertEqual(self.asyncio_mock.call_count, 1)
        self.assertEqual(self.run_until.run_until_complete.call_count, 1)
        self.assertEqual(self.check_samples.call_count, 1)

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Some entries in BioSamples are orphan",
            email.subject)

    # Test a non blocking instance
    @patch("redis.lock.Lock.acquire", return_value=False)
    def test_search_orphan_nb(self, my_lock):
        """Test SearchOrphanTask while a lock is present"""

        res = self.my_task.run()

        # assert database is locked
        self.assertEqual(res, "%s already running!" % (self.my_task.name))

        # assert function not called
        self.assertEqual(self.asyncio_mock.call_count, 0)
        self.assertEqual(self.run_until.run_until_complete.call_count, 0)
        self.assertEqual(self.check_samples.call_count, 0)
