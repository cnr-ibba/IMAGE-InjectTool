#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 14:14:06 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis
import traceback
import pyUSIrest.client

from celery import chord
from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.utils import timezone

from common.constants import ERROR, READY, SUBMITTED, COMPLETED
from common.tasks import BaseTask, NotifyAdminTaskMixin
from image.celery import app as celery_app
from uid.models import Animal
from submissions.tasks import SubmissionTaskMixin

from ..helpers import get_auth
from ..models import (
    Submission as USISubmission, SubmissionData as USISubmissionData)

# Get an instance of a logger
logger = get_task_logger(__name__)

# how many sample for submission
MAX_SAMPLES = 100


class SubmissionError(Exception):
    """Exception call for Error with submissions"""

    pass


# HINT: move into helper module?
class SubmissionHelper():
    """
    An helper class for submission task, used to deal with pyUSIrest
    """

    # define my class attributes
    def __init__(self, submission_id):

        # ok those are my default class attributes
        self.submission_id = submission_id
        self.submission_obj = None
        self.token = None

        # here are pyUSIrest object
        self.auth = None
        self.root = None

        # here I will track a USI submission
        self.usi_submission = None

        # here I will store samples already submitted
        self.submitted_samples = {}

        # get a submission object
        self.submission_obj = USISubmission.objects.get(
            pk=self.submission_id)

        # HINT: should I check my status?

    @property
    def owner(self):
        """Recover owner from a submission object related with a UID
        Submission

        Returns:
            :py:attr:`Submission.owner`: a django
            :py:class:`django.contrib.auth.models.User` object
        """

        return self.submission_obj.uid_submission.owner

    @property
    def team_name(self):
        """Recover team_name from a submission object

        Returns:
            str: the team name"""

        return self.owner.biosample_account.team.name

    @property
    def usi_submission_name(self):
        """Get/set biosample submission id from database

        Returns:
            str: the biosample USI submission identifier"""

        return self.submission_obj.usi_submission_name

    @usi_submission_name.setter
    def usi_submission_name(self, name):

        self.submission_obj.usi_submission_name = name
        self.submission_obj.save()

    def read_token(self):
        """Read token from REDIS database and set root attribute with a
        pyUSIrest.client.Root instance

        Returns:
            str: the read token"""

        # read biosample token from redis database
        client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB)

        # infere key from submission data
        key = "token:submission:{submission_id}:{user}".format(
            submission_id=self.submission_obj.uid_submission.id,
            user=self.owner)

        # create a new auth object
        logger.debug("Reading token for '%s'" % self.owner)

        # getting token from redis db and set submission data
        self.token = client.get(key).decode("utf8")

        # get a root object with auth
        self.auth = get_auth(token=self.token)

        logger.debug("getting biosample root")
        self.root = pyUSIrest.client.Root(auth=self.auth)

        return self.token

    def start_submission(self):
        """
        Get a USI submission document. Recover submission if possible,
        create a new one if not defined. If recovered submission is
        closed, raise an error
        """

        if not self.recover_submission():
            self.create_submission()

        return self.usi_submission

    def recover_submission(self):
        """Try to recover a USI submission document or raise Exception. If
        not defined, return false"""

        # If no usi_submission_name, return False
        if not self.usi_submission_name:
            return False

        logger.info("Recovering submission %s for team %s" % (
            self.usi_submission_name,
            self.team_name))

        # get the same submission object
        self.usi_submission = self.root.get_submission_by_name(
            submission_name=self.usi_submission_name)

        # check that a submission is still editable
        if self.usi_submission.status != "Draft":
            raise SubmissionError(
                "Cannot recover submission '%s': current status is '%s'" % (
                   self.usi_submission_name,
                   self.usi_submission.status))

        # read already submitted samples
        self.read_samples()

        return True

    def create_submission(self):
        """Create a new USI submission object

        Returns:
            :py:class:`pyUSIrest.client.Submission` a pyUSIrest submission
            object
        """

        # getting team
        logger.debug("getting team '%s'" % (self.team_name))
        team = self.root.get_team_by_name(self.team_name)

        # create a new submission
        logger.info("Creating a new submission for '%s'" % (team.name))
        self.usi_submission = team.create_submission()

        # track submission_id in table
        self.usi_submission_name = self.usi_submission.name

        # return USI submission document
        return self.usi_submission

    def read_samples(self):
        """Read sample in a USI submission document and set submitted_samples
        attribute"""

        # read already submitted samples
        logger.debug("Getting info on samples...")
        samples = self.usi_submission.get_samples()
        logger.debug("Got %s samples" % (len(samples)))

        for sample in samples:
            self.submitted_samples[sample.alias] = sample

        return self.submitted_samples

    def create_or_update_sample(self, model):
        """Add or patch a sample into USI submission document. Can be
        animal or sample

        Args:
            model (:py:class:`uid.mixins.BioSampleMixin`): An animal or
                sample object"""

        # alias is used to reference the same objects
        alias = model.biosample_alias

        # check in my submitted samples
        if alias in self.submitted_samples:
            # patch sample
            logger.info("Patching %s" % (alias))

            # get usi sample
            sample = self.submitted_samples[alias]
            sample.patch(model.to_biosample())

        else:
            sample = self.usi_submission.create_sample(
                model.to_biosample())

            self.submitted_samples[alias] = sample

        # update sample status
        model.status = SUBMITTED
        model.last_submitted = timezone.now()
        model.save()

    def add_samples(self):
        """Iterate over sample data (animal/sample) and call
        create_or_update_sample (if model is in READY state)"""

        # iterate over sample data
        for submission_data in self.submission_obj.submission_data\
                .order_by('id'):
            # get model for simplicity
            model = submission_data.content_object

            if model.status == READY:
                logger.debug("Adding %s %s to submission %s" % (
                    model._meta.verbose_name,
                    model,
                    self.usi_submission_name))
                self.create_or_update_sample(model)

            else:
                logger.debug("Ignoring %s %s" % (
                    model._meta.verbose_name, model))

    def mark_submission(self, status, message):
        self.submission_obj.status = status
        self.submission_obj.message = message
        self.submission_obj.save()

    def mark_fail(self, message):
        """Set a :py:const:`ERROR <common.constants.ERROR>` status for
        :py:class:`biosample.models.Submission` and a message"""

        self.mark_submission(ERROR, message)

    def mark_success(self, message="Waiting for biosample validation"):
        """Set a :py:const:`SUBMITTED <common.constants.SUBMITTED>`
        :py:class:`biosample.models.Submission` and a message"""

        self.mark_submission(SUBMITTED, message)


class SubmitTask(NotifyAdminTaskMixin, BaseTask):
    name = "Submit to Biosample"
    description = """Submit to Biosample using USI"""

    def run(self, usi_submission_id):
        """Run task. Instantiate a SubmissionHelper with the provided
        :py:class:`biosample.models.Submission` id. Read token from database,
        start or recover a submission, add samples to it and then mark a
        status for it
        """

        # get a submission helper object
        submission_helper = SubmissionHelper(submission_id=usi_submission_id)

        # No retries, we expect always success
        try:
            submission_helper.read_token()
            submission_helper.start_submission()
            submission_helper.add_samples()
            submission_helper.mark_success()

        except ConnectionError as exc:
            logger.error("Error in biosample submission: %s" % exc)
            message = "Errors in EBI API endpoints. Please try again later"
            logger.error(message)

            # track message in submission object
            submission_helper.mark_submission(READY, message)

        # TODO: should I rename this exception with a more informative name
        # when token expires during a submission?
        except RuntimeError as exc:
            logger.error("Error in biosample submission: %s" % exc)
            message = (
                "Your token is expired: please submit again to resume "
                "submission")
            logger.error(message)

            # track message in submission object
            submission_helper.mark_submission(READY, message)

        except Exception as exc:
            logger.error("Unmanaged error: %s" % exc)
            # get exception info
            einfo = traceback.format_exc()

            # track traceback in message
            submission_helper.mark_fail(einfo)

        return "success", usi_submission_id


# HINT: move into helper module?
class SplitSubmissionHelper():
    """
    helper class to split py:class`uid.models.Submission` data in
    bacthes limited in sizes"""

    def __init__(self, uid_submission):
        self.counter = 0
        self.uid_submission = uid_submission
        self.usi_submission = None
        self.submission_ids = []

    def process_data(self):
        """Add animal and its samples to a submission"""

        for animal in Animal.objects.filter(
                submission=self.uid_submission):

            # add animal if not yet submitted, or patch it
            if animal.status == READY:
                self.add_to_submission_data(animal)

            else:
                # already submitted, so could be ignored
                logger.debug("Ignoring animal %s" % (animal))

            # Add their specimen
            for sample in animal.sample_set.all():
                # add sample if not yet submitted
                if sample.status == READY:
                    self.add_to_submission_data(sample)

                else:
                    # already submittes, so could be ignored
                    logger.debug("Ignoring sample %s" % (sample))

            # end of cicle for animal.

    def create_submission(self):
        """
        Create a new :py:class:`biosample.models.Submission` object and
        set sample counter to 0"""

        self.usi_submission = USISubmission.objects.create(
            uid_submission=self.uid_submission,
            status=READY)

        # track object pks
        self.usi_submission.refresh_from_db()
        self.submission_ids.append(self.usi_submission.id)

        logger.debug("Created submission %s" % (self.usi_submission))

        # reset couter object
        self.counter = 0

    def model_in_submission(self, model):
        """
        Check if :py:class:`uid.mixins.BioSampleMixin` is already in an
        opened submission"""

        logger.debug("Searching %s %s in submissions" % (
            model._meta.verbose_name,
            model))

        # get content type
        ct = ContentType.objects.get_for_model(model)

        # define a queryset
        data_qs = USISubmissionData.objects.filter(
            content_type=ct,
            object_id=model.id)

        # exclude opened submission
        data_qs = data_qs.exclude(submission__status__in=[COMPLETED])

        if data_qs.count() == 1:
            usi_submission = data_qs.first().submission

            logger.debug("Found %s %s in %s" % (
                model._meta.verbose_name,
                model,
                usi_submission))

            # mark this batch to be called like it was created
            if usi_submission.id not in self.submission_ids:
                self.submission_ids.append(usi_submission.id)

                logger.debug(
                    "Reset status for submission %s" % (usi_submission))
                usi_submission.status = READY
                usi_submission.save()

            return True

        elif data_qs.count() >= 1:
            raise SubmissionError(
                "More than one submission opened for %s %s" % (
                    model._meta.verbose_name,
                    model))

        else:
            # no sample in data. I could append model into submission
            logger.debug("No %s %s in submission data" % (
                model._meta.verbose_name,
                model))
            return False

    def add_to_submission_data(self, model):
        """Add a :py:class:`uid.mixins.BioSampleMixin` to a
        :py:class:`biosample.models.Submission` object, or create a new
        one if there are more samples than required"""

        # get model type (animal or sample)
        model_type = model._meta.verbose_name

        # check if model is already in an opened submission
        if self.model_in_submission(model):
            logger.info("Ignoring %s %s: already in a submission" % (
                model_type,
                model))
            return

        # Create a new submission if necessary
        if self.usi_submission is None:
            self.create_submission()

        # every time I split data in chunks I need to call the
        # submission task. Do it only on animals, to prevent
        # to put samples in a different submission
        if model_type == 'animal' and self.counter >= MAX_SAMPLES:
            self.create_submission()

        logger.info("Appending %s %s to %s" % (
            model._meta.verbose_name,
            model,
            self.usi_submission))

        # add object to submission data and updating counter
        USISubmissionData.objects.create(
            submission=self.usi_submission,
            content_object=model)

        self.counter += 1


class SplitSubmissionTask(SubmissionTaskMixin, NotifyAdminTaskMixin, BaseTask):
    """Split submission data in chunks in order to submit data through
    multiple tasks/processes and with smaller submissions"""

    name = "Split submission data"
    description = """Split submission data in chunks"""
    action = "biosample submission"

    def run(self, submission_id):
        """Call :py:class:`SplitSubmissionHelper` to split
        :py:class:`uid.models.Submission` data.
        Call :py:class:`SubmitTask` for each
        batch of data and then call :py:class:`SubmissionCompleteTask` after
        all data were submitted"""

        logger.info("Starting %s for submission %s" % (
            self.name, submission_id))

        uid_submission = self.get_uid_submission(submission_id)

        # call an helper class to create database objects
        submission_data_helper = SplitSubmissionHelper(uid_submission)

        # iterate over animal and samples
        submission_data_helper.process_data()

        # prepare to launch chord tasks
        submissioncomplete = SubmissionCompleteTask()

        # assign kwargs to chord
        callback = submissioncomplete.s(uid_submission_id=submission_id)

        submit = SubmitTask()
        header = [submit.s(pk) for pk in submission_data_helper.submission_ids]

        logger.debug("Preparing chord for %s tasks" % len(header))

        # call chord task. Chord will be called only after all tasks
        res = chord(header)(callback)

        logger.info(
            "Start submission chord process for %s with task %s" % (
                uid_submission,
                res.task_id))

        logger.info("%s completed" % self.name)

        # return a status
        return "success"


class SubmissionCompleteTask(
        SubmissionTaskMixin, NotifyAdminTaskMixin, BaseTask):
    """Update submission status after batch submission"""

    name = "Complete Submission Process"
    description = """Check submission status and update stuff"""
    action = "biosample submission"

    def run(self, *args, **kwargs):
        """Fetch submission data and then update
        :py:class:`uid.models.Submission` status"""

        # those are the output of SubmitTask, as a tuple of
        # biosample.model.Submission.pk and "success"
        submission_statuses = args[0]

        # get UID submission
        uid_submission = self.get_uid_submission(kwargs['uid_submission_id'])

        # mark as completed if submission_statuses is empty, for example when
        # submitting a uid submission with no data
        if not submission_statuses:
            message = "Submission %s is empty!" % uid_submission
            logger.warning(message)

            # update submission status. No more queries on this
            self.update_submission_status(
                uid_submission, ERROR, message)

            return "success"

        # submission_statuses will be an array like this
        # [("success", 1), ("success"), 2]
        usi_submission_ids = [status[1] for status in submission_statuses]

        # fetch data from database
        submission_qs = USISubmission.objects.filter(
            pk__in=usi_submission_ids)

        # annotate biosample submission by statuses
        statuses = {}

        for res in submission_qs.values('status').annotate(
                count=Count('status')):
            statuses[res['status']] = res['count']

        # check for errors in submission. Those are statuses setted by
        # SubmitTask
        if ERROR in statuses:
            # submission failed
            logger.info("Submission %s failed" % uid_submission)

            self.update_message(uid_submission, submission_qs, ERROR)

            # send a mail to the user
            uid_submission.owner.email_user(
                "Error in biosample submission %s" % (
                    uid_submission.id),
                ("Something goes wrong with biosample submission. Please "
                 "report this to InjectTool team\n\n"
                 "%s" % uid_submission.message),
            )

        elif READY in statuses:
            # submission failed
            logger.info("Temporary error for %s" % uid_submission)

            self.update_message(uid_submission, submission_qs, READY)

            # send a mail to the user
            uid_submission.owner.email_user(
                "Temporary error in biosample submission %s" % (
                    uid_submission.id),
                ("Something goes wrong with biosample submission. Please "
                 "try again\n\n"
                 "%s" % uid_submission.message),
            )

        else:
            # Update submission status: a completed but not yet finalized
            # submission
            logger.info("Submission %s success" % uid_submission)

            self.update_message(uid_submission, submission_qs, SUBMITTED)

        return "success"

    def update_message(self, uid_submission, submission_qs, status):
        """Read :py:class:`biosample.models.Submission` message and set
        :py:class:`uid.models.Submission` message"""

        # get error messages for submission
        message = []

        for submission in submission_qs.filter(status=status):
            message.append(submission.message)

        self.update_submission_status(
            uid_submission, status, "\n".join(set(message)))


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(SubmitTask)
celery_app.tasks.register(SplitSubmissionTask)
celery_app.tasks.register(SubmissionCompleteTask)
