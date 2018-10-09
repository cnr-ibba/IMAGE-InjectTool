#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 16:07:58 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os

from decouple import AutoConfig
from celery import task
from celery.utils.log import get_task_logger

from pyEBIrest.auth import Auth
from pyEBIrest.client import Root

from django.conf import settings

from image_app.models import Submission

from .models import ManagedTeam

# Get an instance of a logger
logger = get_task_logger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)

# Set Submission statuses
SUBMITTED = Submission.STATUSES.get_value('submitted')
NEED_REVISION = Submission.STATUSES.get_value('need_revision')


# a function to get a valid auth object
def get_auth(user=None, password=None):
    if not user:
        user = config('USI_MANAGER')
    if not password:
        password = config('USI_MANAGER_PASSWORD')

    return Auth(user, password)


# define a function to get biosample statuses for submissions
@task(bind=True)
def fetch_status(self):
    logger.info("fetch_status started")

    # create a new auth object
    logger.debug("Generate a token for 'USI_MANAGER'")

    auth = get_auth()

    logger.debug("Getting root")

    root = Root(auth)

    # fetching managed teams
    for managed_team in ManagedTeam.objects.all():
        logger.debug("Fetching submission for %s" % managed_team.name)
        team = root.get_team_by_name(team_name=managed_team.name)

        submissions = team.get_submissions()

        for submission in submissions:
            # fetch submission in database
            try:
                # TODO: filter out by status
                obj = Submission.objects.get(
                    biosample_submission_id=submission.name)

            except Submission.DoesNotExist:
                logger.warning(
                    "submission %s is not present in database" % (
                        submission.name))
                continue

            else:
                logger.info(submission)

                # Update submission status if completed
                if submission.submissionStatus == 'Completed':
                    obj.status = SUBMITTED
                    obj.message = "Successful submission into biosample"
                    obj.save()

                    # cicle along samples
                    for sample in submission.get_samples():
                        logger.info(sample)

                        # TODO: fetch biosample ID and save them in name table

                elif submission.submissionStatus == 'Draft':
                    # TODO: check validation. If it is ok, finalize submission
                    # HINT: can I finalize as a manager user?
                    errors = submission.has_errors()

                    if True in errors:
                        logger.error("Errors for submission: %s" % (errors))
                        logger.error("Fix them, then finalize")

                        # Update status
                        obj.status = NEED_REVISION
                        obj.message = "Error in biosample submission"
                        obj.save()

                    else:
                        logger.info("Finalizing submission %s" % (
                            submission.name))
                        submission.finalize()

                else:
                    logger.warning("Unknown status %s for submission %s" % (
                        submission.submissionStatus, submission.name))

                # submission status condition

            # submission present in database

        # submission retrieved in biosample

    # debug
    logger.info("fetch_status completed")

    return "success"