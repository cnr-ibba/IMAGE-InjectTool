#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:22:33 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Useful staff to deal with validation process

"""

from time import sleep

from celery import task
from celery.utils.log import get_task_logger

from submissions.templatetags.submissions_tags import can_validate
from image_app.models import Submission

# Get an instance of a logger
logger = get_task_logger(__name__)

# get available statuses
READY = Submission.STATUSES.get_value('ready')


# a function to perform validation steps
@task(bind=True)
def validate_submission(self, submission_id):
    logger.info("validate_submission started")

    # get submissio object
    submission = Submission.objects.get(pk=submission_id)

    # check submission status
    if not can_validate(submission):
        message = "Can't validate submission %s: current status is %s" % (
                    submission, submission.get_status_display())
        logger.error(message)
        return message

    # TODO: do stuff
    sleep(30)

    # Update submission status
    # TODO: set a proper value for status (READY or NEED_REVISION)
    submission.status = READY
    submission.message = "Submission validated with success"
    submission.save()

    logger.info("validate_submission completed")

    return "success"
