#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 15:30:47 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Send a submission as biosample manager user

"""

import logging

from django.core.management import BaseCommand

import pyUSIrest

from common.constants import SUBMITTED
from image_app.models import Submission

from biosample.helpers import get_manager_auth
from biosample.models import Submission as USISubmission
from biosample.tasks.submission import SplitSubmissionHelper, SubmissionHelper


# Get an instance of a logger
logger = logging.getLogger(__name__)

# change the default level for pyUSIrest logging
logging.getLogger('pyUSIrest.auth').setLevel(logging.INFO)
logging.getLogger('pyUSIrest.client').setLevel(logging.INFO)


class Command(BaseCommand):
    help = 'Submit to biosample a specific submission'

    def add_arguments(self, parser):
        parser.add_argument(
            '--submission',
            required=True,
            type=int)

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Starting biosample_submission...")

        # get a submission from submission id
        submission_id = options['submission']
        submission_obj = Submission.objects.get(pk=submission_id)

        # split data in submission objects like biosample.tasks does
        submission_data_helper = SplitSubmissionHelper(submission_obj)

        # iterate over animal and samples
        submission_data_helper.process_data()

        # get an auth object
        auth = get_manager_auth()

        # get root object
        logger.debug("getting biosample root")
        root = pyUSIrest.client.Root(auth=auth)

        usi_submissions = USISubmission.objects.filter(
            pk__in=submission_data_helper.submission_ids)

        # ok get all biosample.model.Submission and iterate over them
        for usi_submission in usi_submissions:

            # define a submission helper object
            submission_helper = SubmissionHelper(
                submission_id=usi_submission.id)

            # assign class attributes
            submission_helper.auth = auth
            submission_helper.root = root

            # then call methods
            submission_helper.start_submission()
            submission_helper.add_samples()
            submission_helper.mark_success()

        # update submission status
        # TODO: use a biosample.tasks or helper method to do this
        submission_obj.status = SUBMITTED
        submission_obj.message = "Waiting for biosample validation"
        submission_obj.save()

        logger.info("Submission completed!")
