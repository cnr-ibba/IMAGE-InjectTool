#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 16:07:58 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import redis
import celery

from decouple import AutoConfig
from celery import task
from celery.utils.log import get_task_logger

from pyUSIrest.auth import Auth
from pyUSIrest.client import Root

from django.db import transaction
from django.conf import settings
from django.utils import timezone

from image_app.models import Submission, Animal, Sample, STATUSES

# Get an instance of a logger
logger = get_task_logger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)

# Get Submission statuses
SUBMITTED = STATUSES.get_value('submitted')
NEED_REVISION = STATUSES.get_value('need_revision')
COMPLETED = STATUSES.get_value('completed')
WAITING = STATUSES.get_value('waiting')
ERROR = STATUSES.get_value('error')
READY = STATUSES.get_value('ready')


class SubmitTask(celery.Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # get submission_id from task arguments
        submission_id = args[0]

        # get submissio object
        submission_obj = Submission.objects.get(pk=submission_id)

        submission_obj.status = ERROR
        submission_obj.message = "Error in biosample submission: %s" % str(exc)
        submission_obj.save()

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in biosample submission %s" % (submission_id),
            ("Something goes wrong with biosample submission. Please report "
             "this to InjectTool team\n\n %s" % str(exc)),
        )


# a function to submit data into biosample
@task(bind=True, base=SubmitTask)
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

    # call a method to submit data to biosample
    try:
        submit_biosample(token, team_name, submission)

    # retry a task under errors
    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#retrying
    except ConnectionError as exc:
        raise self.retry(exc=exc)

    logger.info("database updated and task finished")
    return "success"


def submit_biosample(token, team_name, submission_obj):
    # reading token in auth
    # TODO: get an auth instance from an helpers method
    auth = Auth(token=token)

    logger.debug("getting biosample root")
    root = Root(auth=auth)

    # getting team
    logger.debug("getting team '%s'" % (team_name))
    team = root.get_team_by_name(team_name)

    # if I'm recovering a submission, get the same submission id
    if (submission_obj.biosample_submission_id is not None and
            submission_obj.biosample_submission_id != ''):

        logger.info("Recovering submission %s for team %s" % (
            submission_obj.biosample_submission_id, team.name))

        # get the same submission object
        submission = root.get_submission_by_name(
            submission_name=submission_obj.biosample_submission_id)

    else:
        # create a new submission
        logger.info("Creating a new submission for %s" % (team.name))
        submission = team.create_submission()

        # track submission_id in table
        submission_obj.biosample_submission_id = submission.name
        submission_obj.save()

    logger.info("Fetching data and add to submission %s" % (
        submission.name))

    # HINT: what happen if a token expire while submitting?
    for animal in Animal.objects.filter(
            name__submission=submission_obj):

        # add animal if not yet submitted
        if animal.name.status != SUBMITTED:
            logger.info("Appending animal %s" % (animal))
            submission.create_sample(animal.to_biosample())

            # update animal status
            animal.name.status = SUBMITTED
            animal.name.last_submitted = timezone.now()
            animal.name.save()

        # Add their specimen
        for sample in animal.sample_set.all():
            # add sample if not yet submitted
            if sample.name.status != SUBMITTED:
                logger.info("Appending sample %s" % (sample))
                submission.create_sample(sample.to_biosample())

                # update sample status
                sample.name.status = SUBMITTED
                sample.name.last_submitted = timezone.now()
                sample.name.save()

    logger.info("submission completed")

    # Update submission status: a completed but not yet finalized submission
    submission_obj.status = SUBMITTED
    submission_obj.message = "Waiting for biosample validation"
    submission_obj.save()


# a function to get a valid auth object
# TODO: create an Auth instance from a token
# TODO: move in helpers module
def get_auth(user=None, password=None):
    """Returns an Auth instance"""

    if not user:
        user = config('USI_MANAGER')

    if not password:
        password = config('USI_MANAGER_PASSWORD')

    return Auth(user, password)


# a function to finalize a submission
def finalize(submission, submission_obj):
    errors = submission.has_errors()

    if True in errors:
        # get sample with errors then update database
        samples = submission.get_samples(has_errors=True)

        for sample in samples:
            # derive pk and table from alias
            table, pk = sample.alias.split("_")
            table, pk = table.capitalize(), int(pk)

            logger.debug("%s in table %s has errors!!!" % (sample, table))

            if table == 'Sample':
                sample_obj = Sample.objects.get(pk=pk)
                sample_obj.name.status = NEED_REVISION
                sample_obj.name.save()

            elif table == 'Animal':
                animal_obj = Animal.objects.get(pk=pk)
                animal_obj.name.status = NEED_REVISION
                animal_obj.name.save()

            else:
                raise Exception("Unknown table %s" % (table))

        logger.error("Errors for submission: %s" % (submission))
        logger.error("Fix them, then finalize")

        # Update status for submission
        submission_obj.status = NEED_REVISION
        submission_obj.message = "Error in biosample submission"
        submission_obj.save()

    else:
        logger.info("Finalizing submission %s" % (
            submission.name))
        submission.finalize()


# a function to retrieve biosample submission
def fetch_biosample_status(queryset):
    logger.info("Searching for submissions into biosample")

    # create a new auth object
    logger.debug("Generate a token for 'USI_MANAGER'")
    auth = get_auth()

    logger.debug("Getting root")
    root = Root(auth)

    for submission_obj in queryset:
        logger.info("Processing submission %s" % (submission_obj))

        # fetch a biosample object
        submission = root.get_submission_by_name(
            submission_name=submission_obj.biosample_submission_id)

        # a submission object retrieved by the previous method hasn't the
        # submission status, so I need to follow submissionStatus link
        # TODO: update pyUSIrest to fetch submissionStatus value
        document = submission.follow_url('submissionStatus', auth=auth)

        # Update submission status if completed
        if document.status == 'Completed':
            # cicle along samples
            for sample in submission.get_samples():
                # derive pk and table from alias
                table, pk = sample.alias.split("_")
                table, pk = table.capitalize(), int(pk)

                if table == 'Sample':
                    sample_obj = Sample.objects.get(pk=pk)
                    sample_obj.name.status = COMPLETED
                    sample_obj.name.biosample_id = sample.accession
                    sample_obj.name.save()

                elif table == 'Animal':
                    animal_obj = Animal.objects.get(pk=pk)
                    animal_obj.name.status = COMPLETED
                    animal_obj.name.biosample_id = sample.accession
                    animal_obj.name.save()

                else:
                    raise Exception("Unknown table %s" % (table))

            # update submission
            submission_obj.status = COMPLETED
            submission_obj.message = "Successful submission into biosample"
            submission_obj.save()

            logger.info(
                "Submission %s is now completed and recorded into UID" % (
                    submission))

        elif document.status == 'Draft':
            # check validation. If it is ok, finalize submission
            status = submission.get_status()

            if len(status) == 1 and 'Complete' in status:
                # check for errors and eventually finalize
                finalize(submission, submission_obj)

            else:
                logger.warning(
                    "Biosample validation is not completed yet (%s)" %
                    (status))

        else:
            logger.warning("Unknown status %s for submission %s" % (
                document.status, submission.name))

        # test for submission status

    # cicle for submission_obj

    logger.info("fetch_biosample_status completed")


# define a function to get biosample statuses for submissions
# transaction atomic in order to prevent two fetch_status task run in the same
# time, using select_for_update
@task(bind=True)
@transaction.atomic
def fetch_status(self):
    logger.info("fetch_status started")

    # search for submission with SUBMITTED status. Other submission are not yet
    # finalized. Ensure one process running with locking:
    qs = Submission.objects.select_for_update(
        nowait=True).filter(status=SUBMITTED)

    # check for queryset length
    if qs.count() != 0:
        try:
            # fetch biosample status
            fetch_biosample_status(qs)

        # retry a task under errors
        # http://docs.celeryproject.org/en/latest/userguide/tasks.html#retrying
        except ConnectionError as exc:
            raise self.retry(exc=exc)

    else:
        logger.debug("No pending submission in UID database")

    # debug
    logger.info("fetch_status completed")

    return "success"
