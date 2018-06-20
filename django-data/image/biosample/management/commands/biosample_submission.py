#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 15:30:47 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import sys
import time
import logging
import getpass

from django.core.management import BaseCommand

import pyEBIrest

from image_app.models import Animal

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Submit to biosample'

    def add_arguments(self, parser):
        parser.add_argument(
            '-u',
            '--username',
            type=str,
            required=True,
            help="Your USI username")

        parser.add_argument(
            '--token_file',
            type=str,
            help="A text file containing a valid token")

        # TODO: provide team name by command line

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Called %s" % (sys.argv[1]))

        if options['token_file']:
            with open(options['token_file']) as infile:
                token = infile.read()
                auth = pyEBIrest.Auth(token=token)

        else:
            # creating an authentication object
            auth = pyEBIrest.Auth(
                user=options['username'],
                password=getpass.getpass())

        # TODO: check if provide team belongs to user in auth.claims

        # get root object
        root = pyEBIrest.Root(auth=auth)

        # get an example team
        team = root.get_team_by_name('subs.test-team-3')

        # create a submission
        submission = team.create_submission()

        # get all animal data
        for animal in Animal.objects.filter(
                sample__name__isnull=False).distinct()[:30]:
            logging.info("Appending animal %s to submission" % (animal))
            submission.create_sample(animal.to_biosample())

            # Add their specimen
            for sample in animal.sample_set.all():
                logging.info("Appending sample %s to submission" % (sample))
                submission.create_sample(sample.to_biosample())

        # TODO: check that validations happens and that is OK
        # validation could take time
        logger.info("Sleep for a while...")
        time.sleep(10)

        # finalize submission
        submission.finalize()

        # completed
        logger.info("%s ended" % (sys.argv[1]))
