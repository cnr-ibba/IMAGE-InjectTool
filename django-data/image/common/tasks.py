#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 16:42:24 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis
import logging

from contextlib import contextmanager
from celery.five import monotonic

from django.conf import settings

# Lock expires in 10 minutes
LOCK_EXPIRE = 60 * 10

# Get an instance of a logger
logger = logging.getLogger(__name__)


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
