#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 16:07:58 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import json
import redis
import traceback

from decouple import AutoConfig
from celery.utils.log import get_task_logger

import pyUSIrest.client

from django.conf import settings
from django.utils import timezone

from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Animal
from common.tasks import redis_lock
from common.constants import (
    ERROR, READY, NEED_REVISION, SUBMITTED, COMPLETED)

from .helpers import (
    get_auth, get_manager_auth, parse_image_alias, get_model_object)

# Get an instance of a logger
logger = get_task_logger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)

# a threshold of days to determine a very long task
MAX_DAYS = 5


class SubmissionData(object):
    """An helper class for submission task"""

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

            # get submissio object
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


class SubmitTask(MyTask):
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

    # Ovverride default on failure method
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # create a instance to store submissison data from a submission_id
        submission_data = SubmissionData(submission_id=args[0])

        submission_data.submission_obj.status = ERROR
        submission_data.submission_obj.message = (
            "Error in biosample submission: %s" % str(exc))
        submission_data.submission_obj.save()

        # send a mail to the user with the stacktrace (einfo)
        submission_data.owner.email_user(
            "Error in biosample submission %s" % (
                submission_data.submission_id),
            ("Something goes wrong with biosample submission. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin

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

        # When the status is in this list, I can't submit this sample, since
        # is already submitted by this submission or by a previous one
        # and I don't want to submit the same thing if is not necessary
        not_managed_statuses = [SUBMITTED, COMPLETED]

        # HINT: what happen if a token expire while submitting?
        for animal in Animal.objects.filter(
                name__submission=submission_data.submission_obj):

            # add animal if not yet submitted, or patch it
            if animal.name.status not in not_managed_statuses:
                logger.info("Appending animal %s" % (animal))

                # check if animal is already submitted, otherwise patch
                self.__create_or_update(animal, submission_data)

            else:
                logger.debug("Appending animal %s" % (animal))

            # Add their specimen
            for sample in animal.sample_set.all():
                # add sample if not yet submitted
                if sample.name.status not in not_managed_statuses:
                    logger.info("Appending sample %s" % (sample))

                    # check if sample is already submitted, otherwise patch
                    self.__create_or_update(sample, submission_data)

                else:
                    logger.debug("Ignoring sample %s" % (sample))

        logger.info("submission completed")

        # Update submission status: a completed but not yet finalized
        # submission
        submission_data.submission_obj.status = SUBMITTED
        submission_data.submission_obj.message = (
            "Waiting for biosample validation")
        submission_data.submission_obj.save()

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


class FetchStatusTask(MyTask):
    name = "Fetch USI status"
    description = """Fetch biosample using USI API"""
    lock_id = "FetchStatusTask"

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

        # track data
        usi_objs = {}

        # create a new auth object
        logger.debug("Generate a token for 'USI_MANAGER'")
        usi_objs['auth'] = get_manager_auth()

        logger.debug("Getting root")
        usi_objs['root'] = pyUSIrest.client.Root(usi_objs['auth'])

        for submission_obj in queryset:
            self.fetch_submission_obj(submission_obj, usi_objs)

        logger.info("fetch_queryset completed")

    def fetch_submission_obj(self, submission_obj, usi_objs):
        """Fetch USI from a biosample object"""

        logger.info("Processing submission %s" % (submission_obj))

        # fetch a biosample object
        submission = usi_objs['root'].get_submission_by_name(
            submission_name=submission_obj.biosample_submission_id)

        # Update submission status if completed
        if submission.status == 'Completed':
            # fetch biosample ids with a proper function
            self.complete(submission, submission_obj)

        elif submission.status == 'Draft':
            # check for a long task
            if self.submission_has_issues(submission, submission_obj):
                # return to the caller. I've just marked the submission with
                # errors and sent a mail to the user
                return

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

        elif submission.status == 'Submitted':
            # check for a long task
            if self.submission_has_issues(submission, submission_obj):
                # return to the caller. I've just marked the submission with
                # errors and sent a mail to the user
                return

            logger.info(
                "Submission %s is '%s'. Waiting for biosample "
                "ids" % (submission.id, submission.status))

            # debug submission status
            document = submission.follow_url(
                "processingStatusSummary", usi_objs['auth'])

            logger.debug(
                "Current status for submission %s is %s" % (
                    submission.id, document.data))

        else:
            # HINT: thrown an exception?
            logger.warning("Unknown status %s for submission %s" % (
                submission.status, submission.name))

    def submission_has_issues(self, submission, submission_obj):
        if (timezone.now() - submission_obj.updated_at).days > MAX_DAYS:
            message = (
                "Biosample subission %s remained with the same status "
                "for more than %s days. Please report it to InjectTool "
                "team" % (submission_obj, MAX_DAYS))
            submission_obj.status = ERROR
            submission_obj.message = message
            submission_obj.save()

            logger.error("Errors for submission: %s" % (submission))
            logger.error(message)

            # send a mail to the user
            submission_obj.owner.email_user(
                "Error in biosample submission %s" % (
                    submission_obj.id),
                ("Something goes wrong with biosample submission. Please "
                 "report this to InjectTool team\n\n %s" % str(
                         submission.data)),
            )

            return True

        else:
            return False

    def __sample_has_errors(self, sample, table, pk):
        """Helper metod to mark a (animal/sample) with its own errors. Table
        sould be Animal or Sample to update the approriate object. Sample
        is a USI sample object"""

        # get sample/animal object relying on table name and pk
        sample_obj = get_model_object(table, pk)

        sample_obj.name.status = NEED_REVISION
        sample_obj.name.save()

        # get a USI validation result
        validation_result = sample.get_validation_result()

        # TODO: should I store validation_result error in validation tables?
        errorMessages = validation_result.errorMessages

        # return an error for each object
        return {str(sample_obj): errorMessages}

    # a function to finalize a submission
    def finalize(self, submission, submission_obj):
        # get errors for a submission
        # errors = submission.has_errors()

        # as described by [submission-help #341348] ticket
        # there is an error in Ena which raise errors in accessions. For now
        # I will Ignore Ena errors and force finalizing
        # TOOD: remove ignorelist after USI update
        logger.warning(
            "Ignoring errors from Ena and forcing finalization if possible")
        errors = submission.has_errors(ignorelist=['Ena'])

        # collect all error messages in a list
        messages = []

        if True in errors:
            # get sample with errors then update database
            samples = submission.get_samples(has_errors=True)

            for sample in samples:
                # derive pk and table from alias
                table, pk = parse_image_alias(sample.alias)

                # need to check if this sample/animals has errors or not
                if sample.has_errors():
                    logger.warning(
                        "%s in table %s has errors!!!" % (sample, table))

                    # mark this sample since has problems
                    errorMessages = self.__sample_has_errors(
                        sample, table, pk)

                    # append this into error messages list
                    messages.append(errorMessages)

                # if a sample has no errors, status will be the same

            logger.error("Errors for submission: %s" % (submission))
            logger.error("Fix them, then finalize")

            # report error via mai
            email_body = "Some items needs revision:\n\n" + \
                json.dumps(messages, indent=2)

            # send a mail for this submission
            submission_obj.owner.email_user(
                "Error in biosample submission %s" % (submission_obj.id),
                email_body,
            )

            # Update status for submission
            submission_obj.status = NEED_REVISION
            submission_obj.message = "Error in biosample submission"
            submission_obj.save()

        else:
            # TODO: raising an exception while finalizing will result
            # in a failed task. model and test exception in finalization
            # logger.info("Finalizing submission %s" % (
            #     submission.name))
            # submission.finalize()

            # same for has_error method
            # TOOD: remove ignorelist after USI update
            logger.warning(
                "Ignoring errors from Ena and finalizing submission %s" % (
                    submission.name))
            submission.finalize(ignorelist=['Ena'])

    def complete(self, submission, submission_obj):
        # cicle along samples
        for sample in submission.get_samples():
            # derive pk and table from alias
            table, pk = parse_image_alias(sample.alias)

            # if no accession, return without doing anything
            if sample.accession is None:
                logger.error("No accession found for sample %s" % (sample))
                logger.error("Ignoring submission %s" % (submission))
                return

            # get sample/animal object relying on table name and pk
            sample_obj = get_model_object(table, pk)

            # update statuses
            sample_obj.name.status = COMPLETED
            sample_obj.name.biosample_id = sample.accession
            sample_obj.name.save()

        # update submission
        submission_obj.status = COMPLETED
        submission_obj.message = "Successful submission into biosample"
        submission_obj.save()

        logger.info(
            "Submission %s is now completed and recorded into UID" % (
                submission))


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(SubmitTask)
celery_app.tasks.register(FetchStatusTask)
