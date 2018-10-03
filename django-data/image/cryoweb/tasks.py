#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 11:33:09 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Inspired from

http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html

"""

from contextlib import contextmanager

import redis

from celery import task
from celery.five import monotonic
from celery.utils.log import get_task_logger
from image_app.models import Submission

from .helpers import cryoweb_import, upload_cryoweb
from .models import truncate_database
from django.conf import settings

# get a logger for tasks
logger = get_task_logger(__name__)

# Lock expires in 10 minutes
LOCK_EXPIRE = 60 * 10


@contextmanager
def redis_lock(lock_id, blocking=False):
    # read parameters from settings
    REDIS_CLIENT = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB)

    timeout_at = monotonic() + LOCK_EXPIRE - 3

    lock = REDIS_CLIENT.lock(lock_id, timeout=LOCK_EXPIRE)
    status = lock.acquire(blocking=blocking)

    try:
        yield status

    finally:
        # we take advantage of using add() for atomic locking
        if monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            lock.release()


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

            # TODO: set logging message to talk about tasks
            logger.info(message)

            # always return something
            return "success"

    logger.warning(
        "Cryoweb import already running!")
