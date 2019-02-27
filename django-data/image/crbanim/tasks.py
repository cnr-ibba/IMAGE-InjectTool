#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:37 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from image.celery import app as celery_app, MyTask
from image_app.models import Submission

from .helpers import upload_crbanim

# Get an instance of a logger
logger = get_task_logger(__name__)


class ImportCRBAnimTask(MyTask):
    name = "Import CRBAnim"
    description = """Import CRBAnim data from CRBAnim data file"""

    def run(self, submission_id):
        """a function to upload data into UID"""

        logger.info(
            "Start import from CRBAnim for submission: %s" % submission_id)

        # get a submission object
        submission = Submission.objects.get(pk=submission_id)

        # upload data into UID
        status = upload_crbanim(submission)

        # if something went wrong, uploaded_cryoweb has token the exception
        # ad update submission.message field
        if status is False:
            message = "Error in uploading CRBAnim data"
            logger.error(message)

            # this a failure in my import, not the task itself
            return message

        else:
            message = "Cryoweb import completed for submission: %s" % (
                submission_id)

            # debug
            logger.info(message)

            # always return something
            return "success"


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ImportCRBAnimTask)
