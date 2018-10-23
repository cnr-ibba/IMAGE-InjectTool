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

import pyUSIrest

from image_app.models import Animal

# Get an instance of a logger
logger = logging.getLogger(__name__)

# change the default level for pyUSIrest logging
logging.getLogger('pyUSIrest.auth').setLevel(logging.INFO)
logging.getLogger('pyUSIrest.client').setLevel(logging.INFO)


# helper function to check for errors
def check_submission_status(submission):
    try:
        statuses = submission.get_status()

    except AttributeError as e:
        logger.warn(e)
        # add a fake statuses
        logger.info("Sleep for a while...")
        time.sleep(10)
        statuses = {'Pending': -1}

    return statuses


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

        parser.add_argument(
            '--finalize',
            action='store_true',
            default=False,
            help="Finalize a submission")

        # TODO: provide team name by command line

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Called %s" % (sys.argv[1]))

        if options['token_file']:
            with open(options['token_file']) as infile:
                token = infile.read()
                auth = pyUSIrest.Auth(token=token)

        else:
            # creating an authentication object
            auth = pyUSIrest.Auth(
                user=options['username'],
                password=getpass.getpass())

        # TODO: check if provide team belongs to user in auth.claims

        # get root object
        logger.debug("getting biosample root")
        root = pyUSIrest.Root(auth=auth)

        # get an example team
        team_name = 'subs.test-team-1'
        logger.debug("getting team %s" % (team_name))
        team = root.get_team_by_name(team_name)

        # create a submission
        logger.info("Creating a new submission for %s" % (team.name))
        submission = team.create_submission()

        # get all animal data
        logger.info("Fetching data and add to submission")
        for animal in Animal.objects.filter(
                sample__name__isnull=False).distinct()[:10]:
            logger.info("Appending animal %s to submission" % (animal))
            submission.create_sample(animal.to_biosample())

            # Add their specimen
            for sample in animal.sample_set.all():
                logger.info("Appending sample %s to submission" % (sample))
                submission.create_sample(sample.to_biosample())

        logger.info("Submission completed!")

        # check that validations happens and that is OK
        # validation could take time and the process could generate
        # transitory problems
        statuses = check_submission_status(submission)

        while 'Complete' not in statuses and len(statuses) == 1:
            logger.info("Submission %s: %s" % (submission, statuses))
            logger.info("Sleep for a while...")
            time.sleep(10)
            statuses = check_submission_status(submission)

        logger.info("Submission processed: %s" % (statuses))

        errors = submission.has_errors()

        if True in errors:
            logger.error("Errors for submission: %s" % (errors))
            raise Exception("Submission has error exiting")

        if options['finalize']:
            # finalize submission if there are not errors
            logger.info("Finalizing submission")
            submission.finalize()

        # completed
        logger.info("%s ended" % (sys.argv[1]))
