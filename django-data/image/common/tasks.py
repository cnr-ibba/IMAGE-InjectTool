#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 16:42:24 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis
import traceback

from contextlib import contextmanager
from celery.five import monotonic
from celery.utils.log import get_task_logger

from django.conf import settings
from django.core import management

from image.celery import app as celery_app

from .helpers import send_mail_to_admins

# Lock expires in 10 minutes
LOCK_EXPIRE = 60 * 10

# Get an instance of a logger
logger = get_task_logger(__name__)


class BaseTask(celery_app.Task):
    """Base class to celery tasks. Define logs for on_failure and debug_task"""

    name = None
    description = None
    action = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.name is None:
            self.name = str(self.__class__)

        if self.action is None:
            self.action = str(self.__class__)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

    def debug_task(self):
        # this doesn't throw an error when debugging a task called with run()
        if self.request_stack:
            logger.debug('Request: {0!r}'.format(self.request))


class NotifyAdminTaskMixin():
    """A mixin to send error message to admins"""

    action = None

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Override the default on_failure method"""

        # call base class
        super().on_failure(exc, task_id, args, kwargs, einfo)

        # get exception info
        einfo = traceback.format_exc()

        subject = "Error in %s" % (self.action)
        body = str(einfo)

        send_mail_to_admins(subject, body)


# https://stackoverflow.com/a/51429597
@celery_app.task(bind=True, base=BaseTask)
def clearsessions(self):
    """Cleanup expired sessions by using Django management command."""

    logger.info("Clearing session with celery...")

    # debugging instance
    self.debug_task()

    # calling management command
    management.call_command("clearsessions", verbosity=1)

    # debug
    logger.info("Sessions cleaned!")

    return "Session cleaned with success"


@contextmanager
def redis_lock(lock_id, blocking=False, expire=True):
    """
    This function get a lock relying on a lock name and other status. You
    can describe more process using the same lock name and give exclusive
    access to one of them.

    Args:
        lock_id (str): the name of the lock to take
        blocking (bool): if True, we wait until we have the block, if False
            we returns immediately False
        expire (bool): if True, lock will expire after LOCK_EXPIRE timeout,
            if False, it will persist until lock is released

    Returns:
        bool: True if lock acquired, False otherwise
    """

    # read parameters from settings
    REDIS_CLIENT = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB)

    # this will be the redis lock
    lock = None

    # timeout for the lock (if expire condition)
    timeout_at = monotonic() + LOCK_EXPIRE - 3

    if expire:
        lock = REDIS_CLIENT.lock(lock_id, timeout=LOCK_EXPIRE)

    else:
        lock = REDIS_CLIENT.lock(lock_id, timeout=None)

    status = lock.acquire(blocking=blocking)

    try:
        logger.debug("lock %s acquired is: %s" % (lock_id, status))
        yield status

    finally:
        # we take advantage of using add() for atomic locking
        # don't release the lock if we didn't acquire it
        if status and ((monotonic() < timeout_at and expire) or not expire):
            logger.debug("Releasing lock %s" % lock_id)
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # if no timeout and lock is taken, release it
            lock.release()


class exclusive_task(object):
    """A class decorator to execute an exclusive task by decorating
    celery.tasks.Task.run (run this task once, others
    task calls will return already running message without calling task or
    will wait until other tasks of this type are completed)

    Args:
        task_name (str): task name used for debug
        lock_id (str): the task lock id
        blocking (bool): set task as blocking (wait until no other tasks
            are running. def. False)
        lock_expire (bool): define if lock will expire or not after a
            certain time (def. False)
    """

    def __init__(self, task_name, lock_id, blocking=False, block_expire=False):

        """
        If there are decorator arguments, the function
        to be decorated is not passed to the constructor!
        """
        logger.debug("Setting up ExclusiveTaskDecorator")

        self.task_name = task_name
        self.lock_id = lock_id
        self.blocking = blocking
        self.block_expire = block_expire

    def __call__(self, f):
        """
        If there are decorator arguments, __call__() is only called
        once, as part of the decoration process! You can only give
        it a single argument, which is the function object.
        """
        logger.debug("Decorating function")

        def wrapped_f(*args, **kwargs):
            with redis_lock(
                    self.lock_id,
                    self.blocking,
                    self.block_expire) as acquired:
                if acquired:
                    logger.debug("lock %s acquired" % self.lock_id)

                    # do stuff and return something
                    result = f(*args, **kwargs)

                    logger.debug("lock %s released" % self.lock_id)

                else:
                    # warn user and return a default message
                    result = "%s already running!" % (self.task_name)
                    logger.warning(result)

            return result

        return wrapped_f
