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
from django.utils import timezone

from common.constants import (
    ERROR, READY, SUBMITTED, COMPLETED)
from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Animal
from submissions.helpers import send_message

from ..helpers import get_auth
from ..models import (
    Submission as USISubmission, SubmissionData as USISubmissionData)

# Get an instance of a logger
logger = get_task_logger(__name__)

# how many sample for submission
MAX_SAMPLES = 100


# TODO: promote this to become a common mixin for tasks
class TaskFailureMixin():
    """Mixin candidate to become the common behaviour of task failure which
    mark submission with ERROR status and send message to owner"""

    # Ovverride default on failure method
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # get submission object
        submission_obj = Submission.objects.get(pk=args[0])

        submission_obj.status = ERROR
        submission_obj.message = (
            "Error in biosample submission: %s" % str(exc))
        submission_obj.save()

        # send async message
        send_message(submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in biosample submission %s" % (
                submission_obj.id),
            ("Something goes wrong with biosample submission. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin


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
        Submission"""

        return self.submission_obj.uid_submission.owner

    @property
    def team_name(self):
        """Recover team_name from a submission object"""

        return self.owner.biosample_account.team.name

    @property
    def usi_submission_name(self):
        """Get biosample submission id from database"""

        return self.submission_obj.usi_submission_name

    @usi_submission_name.setter
    def usi_submission_name(self, name):
        """Get biosample submission id from database"""

        self.submission_obj.usi_submission_name = name
        self.submission_obj.save()

    def read_token(self):
        """Read token from REDIS database and set root attribute with a
        pyUSIrest.client.Root instance"""

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
            raise Exception(
                "Cannot recover submission '%s': current status is '%s'" % (
                   self.usi_submission_name,
                   self.usi_submission.status))

        # read already submitted samples
        self.read_samples()

        return True

    def create_submission(self):
        """Create a nre USI submission object"""

        # need to create an empty submission
        # Set self.usi_submission attribute with created document
        # Set a usi_submission_name attribute and returns it

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
        animal or sample"""

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
            self.usi_submission.create_sample(
                model.to_biosample())

        # update sample status
        model.name.status = SUBMITTED
        model.name.last_submitted = timezone.now()
        model.name.save()

    def add_samples(self):
        """Iterate over sample data (animal/sample) and call
        create_or_update_sample"""

        # iterate over sample data
        for submission_data in self.submission_obj.submission_data.all():
            # get model for simplicity
            model = submission_data.content_object

            if model.name.status == READY:
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
        """Set a ERROR status for biosample.models.Submission and a message"""

        self.mark_submission(ERROR, message)

    def mark_success(self, message="Submitted to biosample"):
        """Set a ERROR status for biosample.models.Submission and a message"""

        self.mark_submission(SUBMITTED, message)


class SubmitTask(MyTask):
    name = "Submit to Biosample"
    description = """Submit to Biosample using USI"""

    def run(self, usi_submission_id):
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

        # TODO: should I rename this execption with a more informative name
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


class SplitSubmissionTask(TaskFailureMixin, MyTask):
    """Split a submission data in chunks in order to submit data through
    multiple tasks/processes and with smaller submissions"""

    name = "Split submission data"
    description = """Split submission data in chunks"""

    # HINT: move into helper module?
    class Helper():
        def __init__(self, uid_submission):
            self.counter = 0
            self.uid_submission = uid_submission
            self.usi_submission = None
            self.created_ids = []

        def create_submission(self):
            """Create a new database object and reset counter"""

            self.usi_submission = USISubmission.objects.create(
                uid_submission=self.uid_submission,
                status=READY)

            # track object pks
            self.usi_submission.refresh_from_db()
            self.created_ids.append(self.usi_submission.id)

            # reset couter object
            self.counter = 0

        def model_in_submission(self, model):
            """check if model is already in an opened submission"""

            # get content type
            ct = ContentType.objects.get_for_model(model)

            # define a queryset
            data_qs = USISubmissionData.objects.filter(
                content_type=ct,
                object_id=model.id)

            # exclude opened submission
            data_qs.exclude(submission__status__in=[COMPLETED])

            if data_qs.count() > 0:
                # TODO: mark this batch to be called
                return True

            else:
                # no sample in data. I could append model into submission
                return False

        def add_to_submission_data(self, model):
            # check if model is already in an opened submission
            if self.model_in_submission(model):
                logger.info("Ignoring %s %s: already in a submission" % (
                    model._meta.verbose_name,
                    model))
                return

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
                content_object=model)

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
            if animal.name.status == READY:
                submission_data_helper.add_to_submission_data(animal)

            else:
                # already submittes, so could be ignored
                logger.debug("Ignoring animal %s" % (animal))

            # Add their specimen
            for sample in animal.sample_set.all():
                # add sample if not yet submitted
                if sample.name.status == READY:
                    submission_data_helper.add_to_submission_data(sample)

                else:
                    # already submittes, so could be ignored
                    logger.debug("Ignoring sample %s" % (sample))

            # end of cicle for animal.

        # prepare to launch chord tasks
        callback = submissioncomplete.s()
        submit = SubmitTask()
        header = [submit.s(pk) for pk in submission_data_helper.created_ids]

        # call chord task. Chord will be called only after all tasks
        res = chord(header)(callback)

        logger.info(
            "Start submission chord process for %s with task %s" % (
                uid_submission,
                res.task_id))

        logger.info("%s completed" % self.name)

        # return a status
        return "success"


# TODO: costomize and fix this task placeholder
@celery_app.task
def submissioncomplete(submission_statuses):
    """A placeholder for complete submission object"""

    for submission_status in submission_statuses:
        logger.debug(submission_status)

    return "success"


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(SubmitTask)
celery_app.tasks.register(SplitSubmissionTask)
