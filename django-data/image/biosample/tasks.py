#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 16:07:58 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import redis

from decouple import AutoConfig
from celery import task
from celery.utils.log import get_task_logger

from pyUSIrest.auth import Auth
from pyUSIrest.client import Root

from django.conf import settings
from django.utils import timezone

from image_app.models import Submission, Animal, Name

from .models import ManagedTeam

# Get an instance of a logger
logger = get_task_logger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)

# Get Submission statuses
SUBMITTED = Submission.STATUSES.get_value('submitted')
NEED_REVISION = Submission.STATUSES.get_value('need_revision')
COMPLETED = Submission.STATUSES.get_value('completed')
WAITING = Submission.STATUSES.get_value('waiting')

# get names statuses
NAME_READY = Name.STATUSES.get_value('ready')
NAME_SUBMITTED = Name.STATUSES.get_value('submitted')


# a function to submit data into biosample
@task(bind=True)
def submit(self, submission_id):
    # get submissio object
    submission = Submission.objects.get(pk=submission_id)

    logger.info("Starting submission for user %s" % (
        submission.owner.biosample_account))

    # get info from submission object
    team_name = submission.owner.biosample_account.team.name

    # read biosample token from redis database
    client = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB)

    key = "token:submission:{submission_id}:{user}".format(
        submission_id=submission_id,
        user=submission.owner)

    # create a new auth object
    logger.debug("Reading token for '%s'" % submission.owner)

    # getting token from redis db
    token = client.get(key).decode("utf8")

    # reading token in auth
    auth = Auth(token=token)

    logger.debug("getting biosample root")
    root = Root(auth=auth)

    # getting team
    logger.debug("getting team '%s'" % (team_name))
    team = root.get_team_by_name(team_name)

    # create a submission
    logger.info("Creating a new submission for %s" % (team.name))

    # TODO: if I'm recovering a submission, get the same submission id
    biosample_submission = team.create_submission()

    # track submission_id in table
    submission.biosample_submission_id = biosample_submission.name
    submission.save()

    logger.info("Fetching data and add to submission %s" % (
        biosample_submission.name))

    # HINT: what happen if a token expire while submitting?
    for animal in Animal.objects.filter(
            name__submission=submission,
            name__status=NAME_READY):
        logger.info("Appending animal %s" % (
            animal))
        biosample_submission.create_sample(animal.to_biosample())

        # update animal status
        animal.name.status = NAME_SUBMITTED
        animal.name.last_submitted = timezone.now()
        animal.name.save()

        # Add their specimen
        for sample in animal.sample_set.filter(
                name__status=NAME_READY):
            logger.info("Appending sample %s" % (sample))
            biosample_submission.create_sample(sample.to_biosample())

            # update sample status
            sample.name.status = NAME_SUBMITTED
            sample.name.last_submitted = timezone.now()
            sample.name.save()

    logger.info("submission completed")

    # Update submission status: a completed but not yet finalized submission
    submission.status = SUBMITTED
    submission.message = "Waiting for biosample validation"
    submission.save()

    logger.info("database updated and task finished")

    return "success"


# a function to get a valid auth object
def get_auth(user=None, password=None):
    if not user:
        user = config('USI_MANAGER')
    if not password:
        password = config('USI_MANAGER_PASSWORD')

    return Auth(user, password)


# a function to finalize a submission
def finalize(submission, obj):
    errors = submission.has_errors()

    if True in errors:
        logger.error("Errors for submission: %s" % (
                submission))
        logger.error("Fix them, then finalize")

        # Update status
        obj.status = NEED_REVISION
        obj.message = "Error in biosample submission"
        obj.save()

    else:
        logger.info("Finalizing submission %s" % (
            submission.name))
        submission.finalize()


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
                obj = Submission.objects.get(
                    biosample_submission_id=submission.name)

            except Submission.DoesNotExist:
                logger.warning(
                    "submission '%s' is not present in database" % (
                        submission.name))
                continue

            else:
                # check submission status. If waiting I'm currentlty submitting
                if obj.status == WAITING:
                    logger.warning(
                        "submission '%s' is currently under submission" % (
                            submission.name))
                    continue

                # check status. If submit, I need to process data. Otherwise
                # I can ignore this submission
                if obj.status != SUBMITTED:
                    logger.info(
                        "Ignoring submission %s: current status is '%s'" % (
                            submission.name, obj.get_status_display()))
                    continue

                logger.info("Processing submission %s" % (submission))

                # Update submission status if completed
                if submission.submissionStatus == 'Completed':
                    obj.status = COMPLETED
                    obj.message = "Successful submission into biosample"
                    obj.save()

                    # cicle along samples
                    for sample in submission.get_samples():
                        logger.info(sample)

                        # TODO: fetch biosample ID and save them in name table

                elif submission.submissionStatus == 'Draft':
                    # check validation. If it is ok, finalize submission
                    status = submission.get_status()

                    if len(status) == 1 and 'Complete' in status:
                        finalize(submission, obj)

                    else:
                        logger.warning(
                            "Biosample validation is not completed yet (%s)" %
                            (status))
                        continue

                else:
                    logger.warning("Unknown status %s for submission %s" % (
                        submission.submissionStatus, submission.name))

                # submission status condition

            # submission present in database

        # submission retrieved in biosample

    # debug
    logger.info("fetch_status completed")

    return "success"
