#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 14:14:06 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis

from celery import chord
from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from common.constants import (
    ERROR, READY, SUBMITTED, COMPLETED)
from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Animal
from submissions.helpers import send_message


from ..models import (
    Submission as USISubmission, SubmissionData as USISubmissionData)

# Get an instance of a logger
logger = get_task_logger(__name__)

# how many sample for submission
MAX_SAMPLES = 100


class SubmissionTaskMixin():
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

        return self.submission_obj.usi_submission_id

    @usi_submission_name.setter
    def usi_submission_name(self, name):
        """Get biosample submission id from database"""

        self.submission_obj.usi_submission_name = name
        self.submission_obj.save()

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

        # need a pyUSIrest.client.Root instance
        # if recovered, read submitted samples with self.read_samples()
        # Set self.usi_submission attribute with recovered document

        return False

    def create_submission(self):
        """Create a nre USI submission object"""

        # need a pyUSIrest.client.Root instance
        # Set self.usi_submission attribute with created document
        # Set a usi_submission_name attribute and returns it

    def read_samples(self):
        """Read sample in a USI submission document and set submitted_samples
        attribute"""

        pass

    def create_or_update_sample(self, model):
        """Add or patch a sample into USI submission document. Can be
        animal or sample"""

        pass

    def mark_fail(self, message):
        """Set a ERROR status for biosample.models.Submission and a message"""

        self.submission_obj.status = ERROR
        self.submission_obj.message = message

    def mark_success(self, message="Submitted to biosample"):
        """Set a ERROR status for biosample.models.Submission and a message"""

        self.submission_obj.status = SUBMITTED
        self.submission_obj.message = message

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

    def add_samples(self):
        """Iterate over sample data (animal/sample) and call
        create_or_update_sample"""

        # iterate over sample data
        for submission_data in self.submission_obj.submission_data.all():
            # get model for simplicity
            model = submission_data.content_object

            if model.name.status == READY:
                self.create_or_update_sample(model)

            else:
                logger.debug("Ignoring %s %s" % (
                    model._meta.verbose_name, model))


class SubmitTask(MyTask):
    name = "Submit to Biosample"
    description = """Submit to Biosample using USI"""

    def run(self, usi_submission_id):
        # get a submission helper object
        submission_helper = SubmissionHelper(submission_id=usi_submission_id)

        # TODO: set a try-cacth block. No retries, we expect always success
        submission_helper.read_token()
        submission_helper.start_submission()
        submission_helper.add_samples()


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
