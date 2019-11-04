#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 17 14:19:38 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import json
import logging
import sys

from django.core.management import BaseCommand

from uid.models import Submission, Animal

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Get a JSON for biosample submission'

    def add_arguments(self, parser):
        parser.add_argument(
            '--outfile',
            default=sys.stdout,
            type=str)

        parser.add_argument(
            '--submission',
            required=True,
            type=int)

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Called get_json_for_biosample")

        # get a submission from submission id
        submission_id = options['submission']
        submission = Submission.objects.get(pk=submission_id)

        # get all biosample data for animals
        animals_json = []
        samples_json = []

        # a more limited subset
        for animal in Animal.objects.filter(submission=submission):
            animals_json += [animal.to_biosample()]

            # get samples data and add to a list
            for sample in animal.sample_set.all():
                samples_json += [sample.to_biosample()]

        # collect all data in a dictionary
        biosamples = {'sample': animals_json + samples_json}

        # open handle if necessary
        if options['outfile'] == sys.stdout:
            handle = options['outfile']

        else:
            handle = open(options['outfile'], 'w')

        json.dump(biosamples, handle, indent=2)

        # end the script
        logger.info("get_json_for_biosample ended")
