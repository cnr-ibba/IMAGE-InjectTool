#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 16:07:58 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import redis

from decouple import AutoConfig
from celery.utils.log import get_task_logger

import pyUSIrest.client

from django.conf import settings
from django.utils import timezone

from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Animal, Sample, STATUSES
from common.tasks import redis_lock

from .helpers import get_auth, get_manager_auth

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


class SubmitTask(MyTask):
    name = "Submit to Biosample"
    description = """Submit to Biosample using USI"""

    # define my class attributes
    def __init__(self, *args, **kwargs):
        super(SubmitTask, self).__init__(*args, **kwargs)

        # ok those are my default class attributes
        self.submission_id = None
        self.submission_obj = None
        self.token = None
        self.team_name = None

        # here I will store samples already submitted
        self.submitted_samples = {}

        # here I will track a USI submission
        self.usi_submission = None
        self.usi_root = None

    # Ovverride default on failure method
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        self.submission_obj.status = ERROR
        self.submission_obj.message = (
            "Error in biosample submission: %s" % str(exc))
        self.submission_obj.save()

        # send a mail to the user with the stacktrace (einfo)
        self.submission_obj.owner.email_user(
            "Error in biosample submission %s" % (self.submission_id),
            ("Something goes wrong with biosample submission. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

    def run(self, submission_id):
        """This function is called when delay is called"""

        # assign my submission id
        self.submission_id = submission_id

        # call innner merthod and return results
        return self.submit()

    # a function to submit data into biosample
    def submit(self):
        # get submissio object
        self.submission_obj = Submission.objects.get(pk=self.submission_id)

        logger.info("Starting submission for user %s" % (
            self.submission_obj.owner.biosample_account))

        # get info from submission object
        self.team_name = self.submission_obj.owner.biosample_account.team.name

        # read biosample token from redis database
        client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB)

        key = "token:submission:{submission_id}:{user}".format(
            submission_id=self.submission_id,
            user=self.submission_obj.owner)

        # create a new auth object
        logger.debug("Reading token for '%s'" % self.submission_obj.owner)

        # getting token from redis db
        self.token = client.get(key).decode("utf8")

        # call a method to submit data to biosample
        try:
            self.submit_biosample()

        # retry a task under errors
        # http://docs.celeryproject.org/en/latest/userguide/tasks.html#retrying
        except ConnectionError as exc:
            raise self.retry(exc=exc)

        logger.info("database updated and task finished")

        # return a status
        return "success"

    def submit_biosample(self):
        # reading token in auth
        auth = get_auth(token=self.token)

        logger.debug("getting biosample root")
        self.usi_root = pyUSIrest.client.Root(auth=auth)

        # if I'm recovering a submission, get the same submission id
        if (self.submission_obj.biosample_submission_id is not None and
                self.submission_obj.biosample_submission_id != ''):

            usi_submission_name = self.__recover_submission()

        else:
            # get a new USI submission
            usi_submission_name = self.__create_submission()

        logger.info("Fetching data and add to submission %s" % (
            usi_submission_name))

        # HINT: what happen if a token expire while submitting?
        for animal in Animal.objects.filter(
                name__submission=self.submission_obj):

            # add animal if not yet submitted, or patch it
            if animal.name.status != SUBMITTED:
                logger.info("Appending animal %s" % (animal))

                # check if animal is already submitted, otherwise patch
                self.__create_or_update(animal)

            # Add their specimen
            for sample in animal.sample_set.all():
                # add sample if not yet submitted
                if sample.name.status != SUBMITTED:
                    logger.info("Appending sample %s" % (sample))

                    # check if sample is already submitted, otherwise patch
                    self.__create_or_update(sample)

        logger.info("submission completed")

        # Update submission status: a completed but not yet finalized
        # submission
        self.submission_obj.status = SUBMITTED
        self.submission_obj.message = "Waiting for biosample validation"
        self.submission_obj.save()

    # helper function to create or update a biosample record
    def __create_or_update(self, sample_obj):
        """Create or update a sample (or a animal) in USI"""

        # alias could be animal_XXX or a biosample id
        alias = sample_obj.get_biosample_id()

        # check in my submitted samples
        if alias in self.submitted_samples:
            # patch sample
            logger.info("Patching %s" % (alias))

            # get usi sample
            sample = self.submitted_samples[alias]
            sample.patch(sample_obj.to_biosample())

        else:
            self.usi_submission.create_sample(sample_obj.to_biosample())

        # update sample status
        sample_obj.name.status = SUBMITTED
        sample_obj.name.last_submitted = timezone.now()
        sample_obj.name.save()

    def __recover_submission(self):
        logger.info("Recovering submission %s for team %s" % (
            self.submission_obj.biosample_submission_id, self.team_name))

        # get the same submission object
        usi_submission_name = self.submission_obj.biosample_submission_id

        self.usi_submission = self.usi_root.get_submission_by_name(
            submission_name=usi_submission_name)

        # check that a submission is still editable
        if self.usi_submission.status != "Draft":
            logger.warning(
                "Error for submission '%s': current status is '%s'" % (
                    usi_submission_name, self.usi_submission.status))

            # I can't modify this submission so:
            return self.__create_submission()

        # read already submitted samples
        logger.debug("Getting info on samples...")
        samples = self.usi_submission.get_samples()
        logger.debug("Got %s samples" % (len(samples)))

        for sample in samples:
            self.submitted_samples[sample.alias] = sample

        # return usi biosample id
        return usi_submission_name

    def __create_submission(self):
        # getting team
        logger.debug("getting team '%s'" % (self.team_name))
        team = self.usi_root.get_team_by_name(self.team_name)

        # create a new submission
        logger.info("Creating a new submission for %s" % (team.name))
        self.usi_submission = team.create_submission()

        # track submission_id in table
        usi_submission_name = self.usi_submission.name

        self.submission_obj.biosample_submission_id = usi_submission_name
        self.submission_obj.save()

        # return usi biosample id
        return usi_submission_name


class FetchStatusTask(MyTask):
    name = "Fetch USI status"
    description = """Fetch biosample using USI API"""
    lock_id = "FetchStatusTask"

    # define my class attributes
    def __init__(self, *args, **kwargs):
        super(FetchStatusTask, self).__init__(*args, **kwargs)

        # ok those are my default class attributes
        self.root = None
        self.auth = None

    def run(self):
        """This function is called when delay is called"""

        # debugging instance
        self.debug_task()

        # forcing blocking condition: Wait until a get a lock object
        with redis_lock(self.lock_id, blocking=False) as acquired:
            if acquired:
                # do stuff and return something
                return self.fetch_status()

        message = "%s already running!" % (self.name)

        logger.warning(message)

        return message

    def fetch_status(self):
        """Fetch status from pending submissions"""

        logger.info("fetch_status started")

        # search for submission with SUBMITTED status. Other submission are
        # not yet finalized. This function need to be called by exclusives
        # tasks
        qs = Submission.objects.filter(status=SUBMITTED)

        # check for queryset length
        if qs.count() != 0:
            try:
                # fetch biosample status
                self.fetch_queryset(qs)

            # retry a task under errors
            # http://docs.celeryproject.org/en/latest/userguide/tasks.html#retrying
            except ConnectionError as exc:
                raise self.retry(exc=exc)

        else:
            logger.debug("No pending submission in UID database")

        # debug
        logger.info("fetch_status completed")

        return "success"

    # a function to retrieve biosample submission
    def fetch_queryset(self, queryset):
        """Fetch biosample against a queryset"""

        logger.info("Searching for submissions into biosample")

        # create a new auth object
        logger.debug("Generate a token for 'USI_MANAGER'")
        self.auth = get_manager_auth()

        logger.debug("Getting root")
        self.root = pyUSIrest.client.Root(self.auth)

        for submission_obj in queryset:
            self.fetch_submission_obj(submission_obj)

        logger.info("fetch_queryset completed")

    def fetch_submission_obj(self, submission_obj):
        """Fetch USI from a biosample object"""

        logger.info("Processing submission %s" % (submission_obj))

        # fetch a biosample object
        submission = self.root.get_submission_by_name(
            submission_name=submission_obj.biosample_submission_id)

        # Update submission status if completed
        if submission.status == 'Submitted':
            # cicle along samples
            for sample in submission.get_samples():
                # derive pk and table from alias
                table, pk = sample.alias.split("_")
                table, pk = table.capitalize(), int(pk)

                # if no accession, return without doing anything
                if sample.accession is None:
                    logger.error("No accession found for sample %s" % (sample))
                    logger.error("Ignoring submission %s" % (submission))
                    return

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

        elif submission.status == 'Draft':
            # check validation. If it is ok, finalize submission
            status = submission.get_status()

            # this mean validation statuses, I want to see completed in all
            # samples
            if len(status) == 1 and 'Complete' in status:
                # check for errors and eventually finalize
                self.finalize(submission, submission_obj)

            else:
                logger.warning(
                    "Biosample validation is not completed yet (%s)" %
                    (status))

        elif submission.status == 'Completed':
            logger.info(
                "Submission %s is 'Completed'. Waiting for biosample "
                "ids" % (submission.id))

            # debug submission status
            document = submission.follow_url(
                "processingStatusSummary", self.auth)

            logger.debug(
                "Current status for submission %s is %s" % (
                    submission.id, document.data))

        else:
            # HINT: thrown an exception?
            logger.warning("Unknown status %s for submission %s" % (
                submission.status, submission.name))

    # a function to finalize a submission
    def finalize(self, submission, submission_obj):
        # get errors for a submission
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

            # send a mail for this submission
            submission_obj.owner.email_user(
                "Error in biosample submission %s" % (submission_obj.id),
                "Some items needs revision",
            )

            # Update status for submission
            submission_obj.status = NEED_REVISION
            submission_obj.message = "Error in biosample submission"
            submission_obj.save()

        else:
            logger.info("Finalizing submission %s" % (
                submission.name))
            submission.finalize()


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(SubmitTask)
celery_app.tasks.register(FetchStatusTask)
