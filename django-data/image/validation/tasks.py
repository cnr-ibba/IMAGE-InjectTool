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

# Get an instance of a logger
logger = get_task_logger(__name__)


# a function to perform validation steps
@task(bind=True)
def validate_submission(self, submission_id):
    logger.info("validate_submission started")

    # TODO: do stuff
    sleep(30)

    logger.info("validate_submission completed")

    return "success"
