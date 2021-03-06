#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 11:25:03 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import json
from collections import Counter, defaultdict

from decouple import AutoConfig
from celery.utils.log import get_task_logger

import pyUSIrest.usi
import pyUSIrest.exceptions

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, F
from django.utils import timezone

from image.celery import app as celery_app
from uid.helpers import parse_image_alias, get_model_object
from uid.models import Submission
from common.tasks import BaseTask, NotifyAdminTaskMixin, exclusive_task
from common.constants import ERROR, NEED_REVISION, SUBMITTED, COMPLETED
from submissions.tasks import SubmissionTaskMixin
from validation.models import ValidationResult, ValidationSummary

from ..helpers import get_manager_auth
from ..models import Submission as USISubmission

# Get an instance of a logger
logger = get_task_logger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)

# a threshold of days to determine a very long task
MAX_DAYS = 5


# HINT: how this class could be similar to SubmissionHelper?
class FetchStatusHelper():
    """Helper class to deal with submission data"""

    # define my class attributes
    def __init__(self, usi_submission, auth):
        """
        Helper function to have info for a biosample.models.Submission

        Args:
            usi_submission (biosample.models.Submission): a biosample
                model Submission instance
            auth: a pyUSIrest.auth.Auth instance
        """

        # ok those are my default class attributes
        self.usi_submission = usi_submission
        self.uid_submission = usi_submission.uid_submission

        # here are pyUSIrest object
        self.auth = auth
        self.root = pyUSIrest.usi.Root(self.auth)

        # here I will track the biosample submission
        self.submission_name = self.usi_submission.usi_submission_name

        logger.info(
            "Getting info for usi submission '%s'" % (self.submission_name))
        self.submission = self.root.get_submission_by_name(
            submission_name=self.submission_name)

    def check_submission_status(self):
        """Check submission status, finalize submission, check errors etc"""

        # reload submission status
        self.usi_submission.refresh_from_db()

        if self.usi_submission.status != SUBMITTED:
            # someone else has taken this task and done something. Ignore!
            logger.warning("Ignoring submission %s current status is %s" % (
                self.usi_submission, self.usi_submission.get_status_display()))
            return

        logger.info("Submission '%s' is currently '%s'" % (
            self.submission_name, self.submission.status))

        # Update submission status if completed
        if self.submission.status == 'Completed':
            # fetch biosample ids with a proper function
            self.complete()

        elif self.submission.status == 'Draft':
            # check for a long task
            if self.submission_has_issues():
                # return to the caller. I've just marked the submission with
                # errors and sent a mail to the user
                return

            # check validation. If it is ok, finalize submission
            status = self.submission.get_status()

            # write status into database
            self.usi_submission.samples_status = dict(status)
            self.usi_submission.save()

            # this mean validation statuses, I want to see completed in all
            # samples
            if len(status) == 1 and 'Complete' in status:
                # check for errors and eventually finalize
                self.finalize()

            else:
                logger.warning(
                    "Biosample validation is not completed yet (%s)" %
                    (status))

        elif self.submission.status == 'Submitted':
            # check for a long task
            if self.submission_has_issues():
                # return to the caller. I've just marked the submission with
                # errors and sent a mail to the user
                return

            logger.info(
                "Submission '%s' is '%s'. Waiting for biosample ids" % (
                    self.submission_name,
                    self.submission.status))

            # debug submission status
            document = self.submission.follow_url(
                "processingStatusSummary", self.auth)

            logger.debug(
                "Current status for submission '%s' is '%s'" % (
                    self.submission_name, document.data))

        elif self.submission.status == 'Processing':
            # check for a long task
            if self.submission_has_issues():
                # return to the caller. I've just marked the submission with
                # errors and sent a mail to the user
                return

            logger.debug(
                "Submission '%s' is '%s'. Still waiting from BioSamples" % (
                    self.submission_name,
                    self.submission.status))

        else:
            # HINT: thrown an exception?
            logger.warning("Unknown status '%s' for submission '%s'" % (
                self.submission.status,
                self.submission_name))

        logger.debug("Checking status for '%s' completed" % (
            self.submission_name))

    def submission_has_issues(self):
        """
        Check that biosample submission has not issues. For example, that
        it will remain in the same status for a long time

        Returns:
            bool: True if an issue is detected
        """

        logger.debug(
            "Check if submission '%s' remained in the same status "
            "for a long time" % (
                self.submission_name))

        if (timezone.now() - self.usi_submission.updated_at).days > MAX_DAYS:
            message = (
                "Biosample submission '%s' remained with the same status "
                "for more than %s days. Please report it to InjectTool "
                "team" % (self.submission_name, MAX_DAYS))

            self.usi_submission.status = ERROR
            self.usi_submission.message = message
            self.usi_submission.save()

            logger.error(
                "Errors for submission: %s" % (
                    self.submission_name))
            logger.error(message)

            return True

        else:
            return False

    def sample_has_errors(self, sample, table, pk):
        """
        Helper metod to mark a (animal/sample) with its own errors. Table
        sould be Animal or Sample to update the approriate object. Sample
        is a USI sample object

        Args:
            sample (pyUSIrest.usi.sample): a USI sample object
            table (str): ``Animal`` or ``Sample``, mean the table where this
                object should be searched
            pk (int): table primary key
        """

        # get sample/animal object relying on table name and pk
        sample_obj = get_model_object(table, pk)

        sample_obj.status = NEED_REVISION
        sample_obj.save()

        # get a USI validation result
        validation_result = sample.get_validation_result()

        # track errors  in validation tables
        errorMessages = validation_result.errorMessages

        # since I validated this object, I have already a ValidationResult
        # object associated to my model
        sample_obj.validationresult.status = 'Error'
        sample_obj.validationresult.messages = [
            "%s: %s" % (k, v) for k, v in errorMessages.items()]
        sample_obj.validationresult.save()

        # need to update ValidationSummary table, since here I know if this
        # is a sample or an animal
        summary = self.uid_submission.validationsummary_set.filter(
            type=table.lower()).first()

        # now update query using django F function. Decrease pass count
        # an increase error count for this object
        # HINT: should I define message here?
        summary.pass_count = F('pass_count') - 1
        summary.error_count = F('error_count') + 1
        summary.issues_count = F('issues_count') + 1
        summary.save()

        # return an error for each object
        return {str(sample_obj): errorMessages}

    def finalize(self):
        """Finalize a submission by closing document and send it to
        biosample"""

        logger.info("Finalizing submission '%s'" % (
            self.submission_name))

        # get errors for a submission
        errors = self.submission.has_errors()

        # collect all error messages in a list
        messages = []

        if True in errors:
            # get sample with errors then update database
            samples = self.submission.get_samples(has_errors=True)

            for sample in samples:
                # derive pk and table from alias
                table, pk = parse_image_alias(sample.alias)

                # need to check if this sample/animals has errors or not
                if sample.has_errors():
                    logger.warning(
                        "%s in table %s has errors!!!" % (sample, table))

                    # mark this sample since has problems
                    errorMessages = self.sample_has_errors(
                        sample, table, pk)

                    # append this into error messages list
                    messages.append(errorMessages)

                # if a sample has no errors, status will be the same

            logger.error(
                "Errors for submission: '%s'" % (self.submission_name))
            logger.error("Fix them, then finalize")

            # report error
            message = json.dumps(messages, indent=2)

            # Update status for biosample.models.Submission
            self.usi_submission.status = NEED_REVISION
            self.usi_submission.message = message
            self.usi_submission.save()

        else:
            # raising an exception while finalizing will result
            # in a failed task.
            # TODO: model and test exception in finalization
            self.submission.finalize()

    def complete(self):
        """Complete a submission and fetch biosample names"""

        logger.info("Completing submission '%s'" % (
            self.submission_name))

        for sample in self.submission.get_samples():
            # derive pk and table from alias
            table, pk = parse_image_alias(sample.alias)

            # if no accession, return without doing anything
            if sample.accession is None:
                logger.error("No accession found for sample '%s'" % (sample))
                logger.error("Ignoring submission '%s'" % (self.submission))
                return

            # get sample/animal object relying on table name and pk
            sample_obj = get_model_object(table, pk)

            # update statuses
            sample_obj.status = COMPLETED
            sample_obj.biosample_id = sample.accession
            sample_obj.save()

        # update submission
        self.usi_submission.status = COMPLETED
        self.usi_submission.message = "Successful submission into biosample"
        self.usi_submission.save()

        logger.info(
            "Submission %s is now completed and recorded into UID" % (
                self.submission))


class FetchStatusTask(NotifyAdminTaskMixin, BaseTask):
    name = "Fetch USI status"
    description = """Fetch biosample using USI API"""

    @exclusive_task(task_name="Fetch USI status", lock_id="FetchStatusTask")
    def run(self):
        """
        This function is called when delay is called. It will acquire a lock
        in redis, so those tasks are mutually exclusive

        Returns:
            str: success if everything is ok. Different messages if task is
            already running or exception is caught"""

        # debugging instance
        self.debug_task()

        # do stuff and return something
        return self.fetch_status()

    def fetch_status(self):
        """
        Fetch status from pending submissions. Called from
        :py:meth:`run`, handles exceptions from USI, select
        all :py:class:`Submission <uid.models.Submission>` objects
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
            except pyUSIrest.exceptions.USIConnectionError as exc:
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
        :py:class:`Submission <uid.models.Submission>` objects). Iterate
        through submission to get USI info. Calls
        :py:class:`FetchStatusHelper`
        """

        logger.debug("get an pyUSIrest.auth.Auth object")

        auth = get_manager_auth()

        logger.info("Searching for submissions into biosample")

        for uid_submission in queryset:
            logger.info("getting USI submission for UID '%s'" % (
                uid_submission))
            usi_submissions = USISubmission.objects.filter(
                uid_submission=uid_submission,
                status=SUBMITTED)

            # HINT: fetch statuses using tasks?
            for usi_submission in usi_submissions:
                status_helper = FetchStatusHelper(usi_submission, auth)
                status_helper.check_submission_status()

            # set the final status for a submission like SubmissionCompleteTask
            retrievalcomplete = RetrievalCompleteTask()

            # assign kwargs to chord
            res = retrievalcomplete.delay(uid_submission_id=uid_submission.id)

            logger.info(
                "Start RetrievalCompleteTask process for '%s' "
                "with task '%s'" % (uid_submission, res.task_id))

        logger.info("fetch_queryset completed")


class RetrievalCompleteTask(SubmissionTaskMixin, BaseTask):
    """Update submission status after fetching status"""

    name = "Complete Retrieval Process"
    description = """Check submission status after retrieval nd update stuff"""
    action = "biosample retrieval"

    def run(self, *args, **kwargs):
        """Fetch submission data and then update UID submission status"""

        logger.info("RetrievalCompleteTask started")

        # get UID submission
        uid_submission = self.get_uid_submission(kwargs['uid_submission_id'])

        # fetch data from database
        submission_qs = USISubmission.objects.filter(
            uid_submission=uid_submission)

        # annotate biosample submission by statuses
        statuses = {}

        for res in submission_qs.values('status').annotate(
                count=Count('status')):
            statuses[res['status']] = res['count']

        if SUBMITTED in statuses:
            # ignoring the other models. No errors thrown until there is
            # as SUBMITTED USISubmission
            logger.info("Submission %s not yet finished" % uid_submission)

            return "success"

        # if there is ANY errors in biosample.models.Submission for a
        # particoular submission, I will mark it as ERROR
        elif ERROR in statuses:
            # submission failed
            logger.info("Submission %s failed" % uid_submission)

            # update validationsummary
            self.update_validationsummary(uid_submission)

            self.update_message(uid_submission, submission_qs, ERROR)

            # send a mail to the user
            subject = "Error in biosample submission %s" % (
                uid_submission.id)
            body = (
                "Something goes wrong with biosample submission. Please "
                "report this to InjectTool team\n\n"
                "%s" % uid_submission.message)

            self.mail_to_owner(uid_submission, subject, body)

        # check if submission need revision
        elif NEED_REVISION in statuses:
            # submission failed
            logger.info("Submission %s failed" % uid_submission)

            # update validationsummary
            self.update_validationsummary(uid_submission)

            self.update_message(uid_submission, submission_qs, NEED_REVISION)

            # send a mail to the user
            subject = "Error in biosample submission %s" % (
                uid_submission.id)
            body = "Some items needs revision:\n\n" + uid_submission.message

            self.mail_to_owner(uid_submission, subject, body)

        elif COMPLETED in statuses and len(statuses) == 1:
            # if all status are complete, the submission is completed
            logger.info(
                "Submission %s completed with success" % uid_submission)

            self.update_message(uid_submission, submission_qs, COMPLETED)

        logger.info("RetrievalCompleteTask completed")

        return "success"

    def update_message(self, uid_submission, submission_qs, status):
        """Read biosample.models.Submission message and set
        uid.models.Submission message relying on status"""

        # get error messages for submission
        message = []

        for submission in submission_qs.filter(status=status):
            message.append(submission.message)

        self.update_submission_status(
            uid_submission,
            status,
            "\n".join(set(message)),
            construct_message=True)

    def update_validationsummary(self, uid_submission):
        """Update validationsummary message after our USI submission is
        completed (with errors or not)"""

        self.__generic_validationsummary(uid_submission, "animal")
        self.__generic_validationsummary(uid_submission, "sample")

    def __generic_validationsummary(self, uid_submission, model):
        # when arriving here, I have processed the USI results and maybe
        # i have update validationresult accordingly
        logger.debug("Update validationsummary(%s) for %s" % (
            model, uid_submission))

        model_type = ContentType.objects.get(app_label='uid', model=model)

        # get validation results querysets
        model_qs = ValidationResult.objects.filter(
            submission=uid_submission,
            content_type=model_type,
            status="Error")

        # ok now prepare messages
        messages_counter = Counter()
        messages_ids = defaultdict(list)

        for item in model_qs:
            for message in item.messages:
                messages_counter.update([message])
                messages_ids[message].append(item.content_object.id)

        # ok preparing to update summary object
        model_summary = ValidationSummary.objects.get(
            submission=uid_submission, type=model)
        messages = []

        # create messages. No offending column since is not always possible
        # to determine a column from USI error. With this, I have a record
        # in ValidationSummary page, but I don't have a link to batch update
        # since is not possible to determine and change a column in my
        # data
        for message, count in messages_counter.items():
            messages.append({
                'message': message,
                'count': count,
                'ids': messages_ids[message],
                'offending_column': ''})

        model_summary.messages = messages
        model_summary.save()


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(FetchStatusTask)
celery_app.tasks.register(RetrievalCompleteTask)
