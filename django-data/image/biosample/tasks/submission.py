#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 14:14:06 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis
from celery.utils.log import get_task_logger

from django.conf import settings

from common.constants import ERROR, SUBMITTED, READY
from image.celery import app as celery_app, MyTask

from ..models import Submission as USISubmission

# Get an instance of a logger
logger = get_task_logger(__name__)


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


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(SubmitTask)
