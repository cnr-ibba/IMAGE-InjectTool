#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 11:33:09 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Inspired from

http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html

"""

from celery import task
from celery.utils.log import get_task_logger
from image_app.models import Submission

from common.tasks import redis_lock

from .helpers import cryoweb_import, upload_cryoweb
from .models import truncate_database

# get a logger for tasks
logger = get_task_logger(__name__)


# clean cryoweb database after calling decorated function
def clean_cryoweb_database(f):
    def wrap(*args, **kwargs):
        result = f(*args, **kwargs)

        # clean database after calling function. If results is None, task
        # wasn't running since a lock was acquired with non-blocking
        if result:
            logger.debug("Cleaning up cryoweb database")
            truncate_database()

        return result

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__

    # return decorated function
    return wrap


@task(bind=True)
@clean_cryoweb_database
def import_from_cryoweb(self, submission_id, blocking=True):
    """
    An exclusive task wich upload a *data-only* cryoweb dump in cryoweb
    database and then fill up :ref:`UID <The Unified Internal Database>`
    tables. After data import (wich could be successful or not) cryoweb
    helper database is cleanded and restored in the original status::

        from cryoweb.tasks import import_from_cryoweb

        # call task asynchronously
        res = import_from_cryoweb.delay(submission_id)

    Args:
        submission_id (int): the submission primary key
        blocking (bool): set task as exclusive or not (def: True)

    Returns:
        str: a message string (ex. success)

    """
    # The cache key consists of the task name and the MD5 digest
    # of the feed URL.
    lock_id = 'ImportFromCryoWeb'

    # TODO: tell that task is started
    logger.info("Start import from cryoweb for submission: %s" % submission_id)

    # get a submission object
    submission = Submission.objects.get(pk=submission_id)

    # forcing blocking cndition: Wait until a get a lock object
    with redis_lock(lock_id, blocking=blocking) as acquired:
        if acquired:
            # upload data into cryoweb database
            status = upload_cryoweb(submission_id)

            # if something went wrong, uploaded_cryoweb has token the exception
            # ad update submission.message field
            if status is False:
                logger.error("Error in uploading cryoweb data")

                # this a failure in my import, not the task itself
                return "error in uploading cryoweb data"

            # load cryoweb data into UID
            # check status
            status = cryoweb_import(submission)

            if status is False:
                logger.error("Error in importing cryoweb data")

                # this a failure in my import, not the task itself
                return "error in importing cryoweb data"

            # modify database status. If I arrive here, everything went ok
            logger.debug("Updating submission %s" % (submission_id))

            message = "Cryoweb import completed for submission: %s" % (
                submission_id)

            # debug
            logger.info(message)

            # always return something
            return "success"

    logger.warning(
        "Cryoweb import already running!")

    return "Cryoweb import already running!"
