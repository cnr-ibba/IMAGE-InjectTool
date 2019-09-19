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

from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from common.constants import NEED_REVISION, ERROR

# Lock expires in 10 minutes
LOCK_EXPIRE = 60 * 10

# Get an instance of a logger
logger = logging.getLogger(__name__)


class BatchFailurelMixin():
    """Common mixin for batch task failure. Need to setup ``batch_type``
    (update/delete) and ``model_type`` (animal/sample)
    """

    batch_type = None
    model_type = None
    submission_cls = None

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        submission_id = args[0]

        logger.error(
            ("%s called with %s" % (self.name, args))
        )

        # get submission object
        submission_obj = self.submission_cls.objects.get(pk=submission_id)

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = (
            "Error in %s batch %s: %s" % (
                self.model_type, self.batch_type, str(exc)))
        submission_obj.save()

        send_message(submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in %s batch %s for submission: %s" % (
                self.model_type, self.batch_type, submission_obj.id),
            ("Something goes wrong in batch %s for %ss. Please report "
             "this to InjectTool team\n\n %s" % (
                self.model_type, self.batch_type, str(einfo))),
        )

        # TODO: submit mail to admin


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
