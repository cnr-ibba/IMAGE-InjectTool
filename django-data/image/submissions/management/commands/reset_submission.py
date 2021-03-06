#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 13:12:19 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

This file will reset a submission by setting loaded state to each sample

"""

import logging

from django.core.management import BaseCommand
from django.utils import timezone

from common.constants import LOADED
from uid.models import Submission, Animal, Sample
from submissions.helpers import send_message
from validation.helpers import construct_validation_message

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reset a submission and its samples'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--submission_id',
            type=int,
            required=True,
            help="The submission id to reset")

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.debug("Starting reset_submission")

        # get a submission object from submission_id
        submission = Submission.objects.get(pk=options['submission_id'])

        # logging info
        logger.info(
            "Resetting submission %s and its animals/samples to 'LOADED'"
            % (submission))

        # get all animals for a submissions
        animals = Animal.objects.filter(submission=submission)

        # update name status
        for animal in animals:
            animal.status = LOADED
            animal.last_changed = timezone.now()
            animal.save()

        # get all samples for a submissions
        samples = Sample.objects.filter(submission=submission)

        # update name status
        for sample in samples:
            sample.status = LOADED
            sample.last_changed = timezone.now()
            sample.save()

        # update submission status
        submission.status = LOADED
        submission.message = "Submission reset to 'Loaded' state"
        submission.save()

        # update submission status
        send_message(
            submission, construct_validation_message(submission)
        )

        # call commands and fill tables.
        logger.debug("reset_submission ended")
