#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 16:42:24 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis

from contextlib import contextmanager
from celery.five import monotonic

from django.conf import settings

from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from common.constants import NEED_REVISION

# Lock expires in 10 minutes
LOCK_EXPIRE = 60 * 10


class BatchUpdateMixin:
    """Mixin to do batch update of fields to fix validation"""

    item_cls = None
    submission_cls = None

    def batch_update(self, submission_id, ids, attribute):
        for id_, value in ids.items():
            if value == '' or value == 'None':
                value = None

            item_object = self.item_cls.objects.get(pk=id_)

            if getattr(item_object, attribute) != value:
                setattr(item_object, attribute, value)
                item_object.save()

        # Update submission
        submission_obj = self.submission_cls.objects.get(pk=submission_id)
        submission_obj.status = NEED_REVISION
        submission_obj.message = "Data updated, try to rerun validation"
        submission_obj.save()

        send_message(
            submission_obj, construct_validation_message(submission_obj)
        )


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
