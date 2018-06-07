#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 18 16:07:38 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Dump all data into biosample format

"""

import sys
import json
import logging

from django.core.management import BaseCommand

from image_app.models import Animal

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Get a JSON for validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--outfile',
            default=sys.stdout,
            type=str)

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Called %s" % (sys.argv[1]))

        # get all biosample data for animals
        animals_json = []
        samples_json = []

        # get animal data and add to a list
        for animal in Animal.objects.all():
            animals_json += [animal.to_validation()]

            # get samples data and add to a list
            for sample in animal.sample_set.all():
                samples_json += [sample.to_validation()]

        # collect all data in a dictionary
        biosamples = {'sample': animals_json + samples_json}

        # open handle if necessary
        if options['outfile'] == sys.stdout:
            handle = options['outfile']

        else:
            handle = open(options['outfile'], 'w')

        json.dump(biosamples, handle, indent=2)

        # call commands and fill tables.
        logger.info("%s ended" % (sys.argv[1]))
