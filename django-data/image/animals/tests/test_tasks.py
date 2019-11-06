#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 14:03:56 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from billiard.einfo import ExceptionInfo

from django.core import mail
from django.test import TestCase

from uid.models import Submission, Animal
from common.constants import NEED_REVISION, STATUSES, ERROR
from common.tests import WebSocketMixin

from .common import AnimalFeaturesMixin
from ..tasks import BatchDeleteAnimals, BatchUpdateAnimals


class BatchDeleteAnimalsTest(
        AnimalFeaturesMixin, WebSocketMixin, TestCase):

    def setUp(self):
        # calling base methods
        super().setUp()

        # get a submission object
        self.submission = Submission.objects.get(pk=1)
        self.submission_id = self.submission.id

        # setting animals to delete
        self.animal_ids = [
            'ANIMAL:::ID:::132713',
            'ANIMAL:::ID:::son',
            'ANIMAL:::ID:::mother']

        # setting tasks
        self.my_task = BatchDeleteAnimals()

    def test_on_failure(self):
        """Testing on failure methods"""

        exc = Exception("Test")
        task_id = "test_task_id"
        args = [self.submission_id, self.animal_ids]
        kwargs = {}
        einfo = ExceptionInfo

        # call on_failure method
        self.my_task.on_failure(exc, task_id, args, kwargs, einfo)

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, ERROR)
        self.assertEqual(
            self.submission.message,
            "Error in batch delete animals: Test")

        # test email sent
        self.assertGreater(len(mail.outbox), 0)

        # read email
        email = mail.outbox[-1]

        self.assertEqual(
            "Error in batch delete animals for submission 1",
            email.subject)

        self.check_message(
            message='Error',
            notification_message='Error in batch delete animals: Test')

    def test_delete_animal(self):
        # calling task and delete a animal
        res = self.my_task.run(
            submission_id=self.submission_id,
            animal_ids=self.animal_ids)

        self.assertEqual(res, "success")

        # no animals
        n_animals = Animal.objects.count()
        self.assertEqual(n_animals, 0)

        # updating validation messages

        # calling a WebSocketMixin method
        # no validation message since no data in validation table
        self.check_message(
            message=STATUSES.get_value_display(NEED_REVISION),
            notification_message=(
                "You've removed %s "
                "animals. Rerun validation please!" % len(self.animal_ids)),
            validation_message={
                'animals': 0, 'samples': 0, 'animal_unkn': 0,
                'sample_unkn': 0, 'animal_issues': 0, 'sample_issues': 0}
        )

    def test_delete_animal_not_exists(self):
        # calling task and delete a animal
        res = self.my_task.run(
            submission_id=self.submission_id,
            animal_ids=["meow"])

        self.assertEqual(res, "success")

        # all animals remain
        n_animals = Animal.objects.count()
        self.assertEqual(n_animals, 3)

        # updating validation messages

        # calling a WebSocketMixin method
        # no validation message since no data in validation table
        self.check_message(
            message=STATUSES.get_value_display(NEED_REVISION),
            notification_message=(
                "You've removed 0 animals. It wasn't possible to find records "
                "with these ids: meow. Rerun validation please!"),
            validation_message={
                'animals': 3, 'samples': 1, 'animal_unkn': 3,
                'sample_unkn': 1, 'animal_issues': 0, 'sample_issues': 0}
        )


class BatchUpdateAnimalsTest(
        AnimalFeaturesMixin, WebSocketMixin, TestCase):

    def setUp(self):
        # calling base methods
        super().setUp()

        # get a submission object
        self.submission = Submission.objects.get(pk=1)
        self.submission_id = self.submission.id

        # setting animals to delete
        self.animal_ids = {
            1: "meow",
            2: "bark",
            3: "None"
        }

        # the attribute to change
        self.attribute = "birth_location"

        # setting tasks
        self.my_task = BatchUpdateAnimals()

    def test_on_failure(self):
        """Testing on failure methods"""

        exc = Exception("Test")
        task_id = "test_task_id"
        args = [self.submission_id, self.animal_ids, self.attribute]
        kwargs = {}
        einfo = ExceptionInfo

        # call on_failure method
        self.my_task.on_failure(exc, task_id, args, kwargs, einfo)

        # check submission status and message
        self.submission.refresh_from_db()

        # check submission.state changed
        self.assertEqual(self.submission.status, ERROR)
        self.assertEqual(
            self.submission.message,
            "Error in batch update animals: Test")

        # test email sent
        self.assertGreater(len(mail.outbox), 0)

        # read email
        email = mail.outbox[-1]

        self.assertEqual(
            "Error in batch update animals for submission 1",
            email.subject)

        self.check_message(
            message='Error',
            notification_message='Error in batch update animals: Test')

    def test_update_animal(self):
        # calling task and update a animal
        res = self.my_task.run(
            submission_id=self.submission_id,
            animal_ids=self.animal_ids,
            attribute=self.attribute)

        self.assertEqual(res, "success")

        # asserting updates
        for key, value in self.animal_ids.items():
            animal = Animal.objects.get(pk=key)
            if value == "None":
                value = None
            self.assertEqual(getattr(animal, self.attribute), value)

        # calling a WebSocketMixin method
        # no validation message since no data in validation table
        self.check_message(
            message=STATUSES.get_value_display(NEED_REVISION),
            notification_message="Data updated, try to rerun validation",
        )
