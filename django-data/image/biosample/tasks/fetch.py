#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 11:25:03 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import json

from decouple import AutoConfig
from celery.utils.log import get_task_logger

import pyUSIrest.client

from django.conf import settings
from django.utils import timezone

from image.celery import app as celery_app, MyTask
from image_app.helpers import parse_image_alias, get_model_object
from image_app.models import Submission
from common.tasks import redis_lock
from common.constants import (
    ERROR, NEED_REVISION, SUBMITTED, COMPLETED)
from submissions.helpers import send_message

from ..helpers import get_manager_auth

# Get an instance of a logger
logger = get_task_logger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)

# a threshold of days to determine a very long task
MAX_DAYS = 5


class FetchStatusTask(MyTask):
    name = "Fetch USI status"
    description = """Fetch biosample using USI API"""
    lock_id = "FetchStatusTask"

    def run(self):
        """
        This function is called when delay is called. It will acquire a lock
        in redis, so those tasks are mutually exclusive

        Returns:
            str: success if everything is ok. Different messages if task is
            already running or exception is caught"""

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
        """
        Fetch status from pending submissions. Called from
        :py:meth:`run`, handles exceptions from USI, select
        all :py:class:`Submission <image_app.models.Submission>` objects
        with :py:const:`SUBMITTED <common.constants.SUBMITTED>` status
        from :ref:`UID <The Unified Internal Database>` and call
        :py:meth:`fetch_queryset` with this data
        """

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
        """Fetch biosample against a queryset (a list of
        :py:const:`SUBMITTED <common.constants.SUBMITTED>`
        :py:class:`Submission <image_app.models.Submission>` objects). Iterate
        through submission to get USI info. Calls
        :py:meth:`fetch_submission_obj`
        """

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
        """
        Check that biosample submission has not issues. For example, that
        it will remain in the same status for a long time

        Args:
            submission (pyUSIrest.client.Submission): a USI submission object
            submission_obj (image_app.models.Submission): an UID submission
                object

        Returns:
            bool: True if an issue is detected

        """

        if (timezone.now() - submission_obj.updated_at).days > MAX_DAYS:
            message = (
                "Biosample subission %s remained with the same status "
                "for more than %s days. Please report it to InjectTool "
                "team" % (submission_obj, MAX_DAYS))
            submission_obj.status = ERROR
            submission_obj.message = message
            submission_obj.save()

            # send async message
            send_message(submission_obj)

            logger.error("Errors for submission: %s" % (submission))
            logger.error(message)

            # send a mail to the user
            submission_obj.owner.email_user(
                "Error in biosample submission %s" % (
                    submission_obj.id),
                ("Something goes wrong: %s" % message),
            )

            return True

        else:
            return False

    def __sample_has_errors(self, sample, table, pk):
        """
        Helper metod to mark a (animal/sample) with its own errors. Table
        sould be Animal or Sample to update the approriate object. Sample
        is a USI sample object

        Args:
            sample (pyUSIrest.client.sample): a USI sample object
            table (str): ``Animal`` or ``Sample``, mean the table where this
                object should be searched
            pk (int): table primary key
        """

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
        errors = submission.has_errors()

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

            # send async message
            send_message(submission_obj)

        else:
            # raising an exception while finalizing will result
            # in a failed task.
            # TODO: model and test exception in finalization
            logger.info("Finalizing submission %s" % (submission.name))
            submission.finalize()

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

        # send async message
        send_message(submission_obj)

        logger.info(
            "Submission %s is now completed and recorded into UID" % (
                submission))


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(FetchStatusTask)
