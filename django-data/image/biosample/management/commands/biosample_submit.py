#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 15:30:47 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Send a submission as biosample manager user

"""

import time
import logging

from django.core.management import BaseCommand
from django.utils import timezone

import pyUSIrest

from common.constants import SUBMITTED
from image_app.models import Submission, Animal

from biosample.helpers import get_manager_auth


# Get an instance of a logger
logger = logging.getLogger(__name__)

# change the default level for pyUSIrest logging
logging.getLogger('pyUSIrest.auth').setLevel(logging.INFO)
logging.getLogger('pyUSIrest.client').setLevel(logging.INFO)


# helper function to check for errors
def check_submission_status(usi_submission):
    try:
        statuses = usi_submission.get_status()

    except AttributeError as e:
        logger.warn(e)
        # add a fake statuses
        logger.info("Sleep for a while...")
        time.sleep(10)
        statuses = {'Pending': -1}

    return statuses


class Command(BaseCommand):
    help = 'Submit to biosample a specific submission'

    def add_arguments(self, parser):
        parser.add_argument(
            '--submission',
            required=True,
            type=int)

        parser.add_argument(
            '--finalize',
            action='store_true',
            default=False,
            help="Finalize a submission")

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Starting biosample_submission...")

        # get a submission from submission id
        submission_id = options['submission']
        submission_obj = Submission.objects.get(pk=submission_id)

        # get team_name from submission object
        team_name = submission_obj.owner.biosample_account.team.name

        # get an auth object
        auth = get_manager_auth()

        # get root object
        logger.debug("getting biosample root")
        root = pyUSIrest.client.Root(auth=auth)

        # get a team
        logger.debug("getting team %s" % (team_name))
        team = root.get_team_by_name(team_name)

        # create a submission
        logger.info("Creating a new submission for %s" % (team.name))
        usi_submission = team.create_submission()

        # track submission_id in table
        usi_submission_name = usi_submission.name

        # track submission id into database
        submission_obj.biosample_submission_id = usi_submission_name
        submission_obj.save()

        # get all animal data
        logger.info("Fetching data and add to submission")

        for animal in Animal.objects.filter(
                name__submission=submission_obj):

            logger.info("Appending animal %s to submission" % (animal))
            usi_submission.create_sample(animal.to_biosample())

            # update animal status
            animal.name.status = SUBMITTED
            animal.name.last_submitted = timezone.now()
            animal.name.save()

            # Add their specimen
            for sample in animal.sample_set.all():
                # add sample if not yet submitted
                logger.info("Appending sample %s to submission" % (sample))
                usi_submission.create_sample(sample.to_biosample())

                # update sample status
                sample.name.status = SUBMITTED
                sample.name.last_submitted = timezone.now()
                sample.name.save()

        logger.info("Submission completed!")

        # update submission status
        submission_obj.status = SUBMITTED
        submission_obj.message = "Waiting for biosample validation"
        submission_obj.save()

        if options['finalize']:
            # check that validations happens and that is OK
            # validation could take time and the process could generate
            # transitory problems
            statuses = check_submission_status(usi_submission)

            while 'Complete' not in statuses and len(statuses) == 1:
                logger.info("Submission %s: %s" % (usi_submission, statuses))
                logger.info("Sleep for a while...")
                time.sleep(10)
                statuses = check_submission_status(usi_submission)

            logger.info("Submission processed: %s" % (statuses))

            errors = usi_submission.has_errors()

            if True in errors:
                logger.error("Errors for submission: %s" % (errors))
                raise Exception("Submission has error exiting")

            # finalize submission if there are not errors
            logger.info("Finalizing submission")
            usi_submission.finalize()

        # completed
        logger.info("biosample_submission completed")
