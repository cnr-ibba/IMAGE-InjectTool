#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 14:03:56 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from image_app.models import Submission, Animal
from common.constants import NEED_REVISION, STATUSES
from common.tests import WebSocketMixin

from .common import AnimalFeaturesMixin
from ..tasks import BatchDeleteAnimals


class BatchDeleteAnimalsTest(
        AnimalFeaturesMixin, WebSocketMixin, TestCase):

    def setUp(self):
        # calling base methods
        super().setUp()

        # get a submission object
        self.submission = Submission.objects.get(pk=1)

        # setting tasks
        self.my_task = BatchDeleteAnimals()

    def test_delete_animal(self):
        animal_ids = [
            'ANIMAL:::ID:::132713',
            'ANIMAL:::ID:::son',
            'ANIMAL:::ID:::mother']

        # calling task and delete a animal
        res = self.my_task.run(
            submission_id=self.submission.id,
            animal_ids=animal_ids)

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
                "animals. Rerun validation please!" % len(animal_ids)))
