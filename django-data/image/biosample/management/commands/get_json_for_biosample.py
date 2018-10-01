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

from image_app.models import Animal

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Get a JSON for biosample submission'

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
        # for animal in Animal.objects.filter():

        # HINT: get a subset of data
        # there are 25 animals and 135 samples with this query
        # for animal in Animal.objects.filter(
        #        breed__supplied_breed__in=["Verzaschese", "Cinta Senese"]):

        # a more limited subset
        for animal in Animal.objects.filter(
                name__name__in=[
                    "ANIMAL:::ID:::VERIT012000024961_2010",
                    "ANIMAL:::ID:::VERIT12000024025_2008",
                    "ANIMAL:::ID:::VERCH1539971_2010",
                    "ANIMAL:::ID:::CS12_1999",
                    "ANIMAL:::ID:::CS05_1999",
                ]):
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

        # call commands and fill tables.
        logger.info("%s ended" % (sys.argv[1]))