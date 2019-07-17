#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 16:07:58 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import redis
import traceback

from decouple import AutoConfig
from celery.utils.log import get_task_logger

import pyUSIrest.client

from django.conf import settings
from django.utils import timezone

from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Animal
from common.constants import (
    ERROR, READY, SUBMITTED, COMPLETED)
from submissions.helpers import send_message

from ..helpers import get_auth
from ..models import (
    Submission as USISubmission, SubmissionData as USISubmissionData)

# Get an instance of a logger
logger = get_task_logger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)

# a threshold of days to determine a very long task
MAX_DAYS = 5

# how many sample for submission
MAX_SAMPLES = 100

# When the status is in this list, I can't submit this sample, since
# is already submitted by this submission or by a previous one
# and I don't want to submit the same thing if is not necessary
DONT_SUBMIT_STATUSES = [SUBMITTED, COMPLETED]


class SubmissionData(object):
    """
    An helper class for submission task, useful to pass parameters like
    submission data between tasks"""

    # define my class attributes
    def __init__(self, *args, **kwargs):

        # ok those are my default class attributes
        self.submission_id = None
        self.submission_obj = None
        self.token = None

        # here I will store samples already submitted
        self.submitted_samples = {}

        # here I will track a USI submission
        self.usi_submission = None
        self.usi_root = None

        if kwargs['submission_id']:
            self.submission_id = kwargs['submission_id']

            # get submission object
            self.submission_obj = Submission.objects.get(
                pk=self.submission_id)

    @property
    def owner(self):
        """Recover owner from a submission object"""

        return self.submission_obj.owner

    @property
    def team_name(self):
        """Recover team_name from a submission object"""

        return self.owner.biosample_account.team.name

    @property
    def biosample_submission_id(self):
        """Get biosample submission id from database"""

        return self.submission_obj.biosample_submission_id


class SubmissionTaskMixin():
    # Ovverride default on failure method
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # create a instance to store submissison data from a submission_id
        submission_data = SubmissionData(submission_id=args[0])

        submission_data.submission_obj.status = ERROR
        submission_data.submission_obj.message = (
            "Error in biosample submission: %s" % str(exc))
        submission_data.submission_obj.save()

        # send async message
        send_message(submission_data.submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_data.owner.email_user(
            "Error in biosample submission %s" % (
                submission_data.submission_id),
            ("Something goes wrong with biosample submission. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin


class SubmitTask(SubmissionTaskMixin, MyTask):
    name = "Submit to Biosample"
    description = """Submit to Biosample using USI"""

    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#instantiation
    # A task is not instantiated for every request, but is registered in
    # the task registry as a global instance. This means that the __init__
    # constructor will only be called once per process, and that the
    # task class is semantically closer to an Actor. if you have a task and
    # you route every request to the same process, then it will keep state
    # between requests. This can also be useful to cache resources, For
    # example, a base Task class that caches a database connection

    def run(self, submission_id):
        """This function is called when delay is called"""

        # create a instance to store submissison data from a submission_id
        submission_data = SubmissionData(submission_id=submission_id)

        # call innner merthod and return results
        return self.submit(submission_data)

    # a function to submit data into biosample
    def submit(self, submission_data):
        logger.info("Starting submission for user %s" % (
            submission_data.owner.biosample_account))

        # read biosample token from redis database
        client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB)

        # infere key from submission data
        key = "token:submission:{submission_id}:{user}".format(
            submission_id=submission_data.submission_id,
            user=submission_data.owner)

        # create a new auth object
        logger.debug("Reading token for '%s'" % submission_data.owner)

        # getting token from redis db and set submission data
        submission_data.token = client.get(key).decode("utf8")

        # call a method to submit data to biosample
        try:
            self.submit_biosample(submission_data)

        except ConnectionError as exc:
            logger.error("Error in biosample submission: %s" % exc)

            message = "Errors in EBI API endpoints. Please try again later"
            logger.error(message)

            # add message to submission. Change status to READY
            submission_data.submission_obj.status = READY
            submission_data.submission_obj.message = message
            submission_data.submission_obj.save()

            # send async message
            send_message(submission_data.submission_obj)

            # get exception info
            einfo = traceback.format_exc()

            # send a mail to the user with the stacktrace (einfo)
            submission_data.owner.email_user(
                "Error in biosample submission %s" % (
                    submission_data.submission_id),
                ("Something goes wrong with biosample submission. Please "
                 "report this to InjectTool team\n\n %s" % str(einfo)),
                )

            return "success"

        # TODO: should I rename this execption with a more informative name
        # when token expires during a submission?
        except RuntimeError as exc:
            logger.error("Error in biosample submission: %s" % exc)

            message = (
                "Your token is expired: please submit again to resume "
                "submission")

            logger.error(message)

            # add message to submission. Change status to READY
            submission_data.submission_obj.status = READY
            submission_data.submission_obj.message = message
            submission_data.submission_obj.save()

            # send async message
            send_message(submission_data.submission_obj)

            # send a mail to the user with the stacktrace (einfo)
            submission_data.owner.email_user(
                "Error in biosample submission %s" % (
                    submission_data.submission_id),
                ("Your token is expired during submission. Click on submit "
                 "button to generate a new token and resume your submission"),
                )

            return "success"

        # retry a task under errors
        # http://docs.celeryproject.org/en/latest/userguide/tasks.html#retrying
        except Exception as exc:
            raise self.retry(exc=exc)

        logger.info("database updated and task finished")

        # return a status
        return "success"

    def submit_biosample(self, submission_data):
        # reading token in auth
        auth = get_auth(token=submission_data.token)

        logger.debug("getting biosample root")
        submission_data.usi_root = pyUSIrest.client.Root(auth=auth)

        # if I'm recovering a submission, get the same submission id
        if (submission_data.biosample_submission_id is not None and
                submission_data.biosample_submission_id != ''):

            usi_submission_name = self.__recover_submission(submission_data)

        else:
            # get a new USI submission
            usi_submission_name = self.__create_submission(submission_data)

        logger.info("Fetching data and add to submission %s" % (
            usi_submission_name))

        # HINT: what happen if a token expire while submitting?
        for animal in Animal.objects.filter(
                name__submission=submission_data.submission_obj):

            # add animal if not yet submitted, or patch it
            if animal.name.status not in DONT_SUBMIT_STATUSES:
                logger.info("Appending animal %s" % (animal))

                # check if animal is already submitted, otherwise patch
                self.__create_or_update(animal, submission_data)

            else:
                # already submittes, so could be ignored
                logger.debug("Ignoring animal %s" % (animal))

            # Add their specimen
            for sample in animal.sample_set.all():
                # add sample if not yet submitted
                if sample.name.status not in DONT_SUBMIT_STATUSES:
                    logger.info("Appending sample %s" % (sample))

                    # check if sample is already submitted, otherwise patch
                    self.__create_or_update(sample, submission_data)

                else:
                    # already submittes, so could be ignored
                    logger.debug("Ignoring sample %s" % (sample))

        logger.info("submission completed")

        # Update submission status: a completed but not yet finalized
        # submission
        submission_data.submission_obj.status = SUBMITTED
        submission_data.submission_obj.message = (
            "Waiting for biosample validation")
        submission_data.submission_obj.save()

        # send async message
        send_message(submission_data.submission_obj)

    # helper function to create or update a biosample record
    def __create_or_update(self, sample_obj, submission_data):
        """Create or update a sample (or a animal) in USI"""

        # alias is used to reference the same objects
        alias = sample_obj.biosample_alias

        # check in my submitted samples
        if alias in submission_data.submitted_samples:
            # patch sample
            logger.info("Patching %s" % (alias))

            # get usi sample
            sample = submission_data.submitted_samples[alias]
            sample.patch(sample_obj.to_biosample())

        else:
            submission_data.usi_submission.create_sample(
                sample_obj.to_biosample())

        # update sample status
        sample_obj.name.status = SUBMITTED
        sample_obj.name.last_submitted = timezone.now()
        sample_obj.name.save()

    def __recover_submission(self, submission_data):
        logger.info("Recovering submission %s for team %s" % (
            submission_data.biosample_submission_id,
            submission_data.team_name))

        # get the same submission object
        usi_submission_name = submission_data.biosample_submission_id

        submission_data.usi_submission = \
            submission_data.usi_root.get_submission_by_name(
                submission_name=usi_submission_name)

        # check that a submission is still editable
        if submission_data.usi_submission.status != "Draft":
            logger.warning(
                "Cannot recover submission '%s': current status is '%s'" % (
                    usi_submission_name,
                    submission_data.usi_submission.status))

            # I can't modify this submission so:
            return self.__create_submission(submission_data)

        # read already submitted samples
        logger.debug("Getting info on samples...")
        samples = submission_data.usi_submission.get_samples()
        logger.debug("Got %s samples" % (len(samples)))

        for sample in samples:
            submission_data.submitted_samples[sample.alias] = sample

        # return usi biosample id
        return usi_submission_name

    def __create_submission(self, submission_data):
        # getting team
        logger.debug("getting team '%s'" % (submission_data.team_name))
        team = submission_data.usi_root.get_team_by_name(
            submission_data.team_name)

        # create a new submission
        logger.info("Creating a new submission for '%s'" % (team.name))
        submission_data.usi_submission = team.create_submission()

        # track submission_id in table
        usi_submission_name = submission_data.usi_submission.name

        submission_data.submission_obj.biosample_submission_id = \
            usi_submission_name
        submission_data.submission_obj.save()

        # return usi biosample id
        return usi_submission_name


class SplitSubmissionTask(SubmissionTaskMixin, MyTask):
    """Split a submission data in chunks in order to submit data through
    multiple tasks/processes and with smaller submissions"""

    name = "Split submission data"
    description = """Split submission data in chunks"""

    class Helper():
        def __init__(self, uid_submission):
            self.counter = 0
            self.uid_submission = uid_submission
            self.usi_submission = None

        def create_submission(self):
            """Create a new database object and reset counter"""

            self.usi_submission = USISubmission.objects.create(
                uid_submission=self.uid_submission,
                status=READY)
            self.counter = 0

        def add_to_submission_data(self, model):
            # Create a new submission if necessary
            if self.usi_submission is None:
                self.create_submission()

            # TODO: every time I split data in chunks I need to call the
            # submission task. I should call this in a chord process, in
            # order to value if submission was completed or not
            if self.counter >= MAX_SAMPLES:
                self.create_submission()

            logger.info("Appending %s %s to %s" % (
                model._meta.verbose_name,
                model,
                self.usi_submission))

            # add object to submission data and updating counter
            USISubmissionData.objects.create(
                submission=self.usi_submission,
                content_object=model,
                status=READY)

            self.counter += 1

    def run(self, submission_id):
        """This function is called when delay is called"""

        logger.info("Starting %s for submission %s" % (
            self.name, submission_id))

        uid_submission = Submission.objects.get(
            pk=submission_id)

        # call an helper class to create database objects
        submission_data_helper = self.Helper(uid_submission)

        for animal in Animal.objects.filter(
                name__submission=uid_submission):

            # add animal if not yet submitted, or patch it
            if animal.name.status not in DONT_SUBMIT_STATUSES:
                submission_data_helper.add_to_submission_data(animal)

            else:
                # already submittes, so could be ignored
                logger.debug("Ignoring animal %s" % (animal))

            # Add their specimen
            for sample in animal.sample_set.all():
                # add sample if not yet submitted
                if sample.name.status not in DONT_SUBMIT_STATUSES:
                    submission_data_helper.add_to_submission_data(sample)

                else:
                    # already submittes, so could be ignored
                    logger.debug("Ignoring sample %s" % (sample))

            # end of cicle for animal.

        logger.info("%s completed" % self.name)

        # return a status
        return "success"


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(SubmitTask)
celery_app.tasks.register(SplitSubmissionTask)
