#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 13:12:19 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

This file will reset a submission by setting loaded state to each sample

"""

import sys
import logging

from django.core.management import BaseCommand

from common.constants import LOADED
from image_app.models import Submission, Name

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
        logger.debug("Called %s" % (sys.argv[1]))

        # get a submission object from submission_id
        submission = Submission.objects.get(pk=options['submission_id'])

        # logging info
        logger.info(
            "Resetting submission %s and its animals/samples to 'LOADED'"
            % (submission))

        # get all names for a submissions
        names = Name.objects.filter(submission=submission)

        # update name status
        for name in names:
            name.status = LOADED
            name.save()

        # update submission status
        submission.status = LOADED
        submission.save()

        # call commands and fill tables.
        logger.debug("%s ended" % (sys.argv[1]))
