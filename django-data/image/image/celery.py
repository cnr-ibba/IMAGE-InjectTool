#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 11 14:34:27 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import redis
import functools

from time import sleep

from celery import Celery, Task
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from django.core import management


logger = get_task_logger(__name__)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image.settings')

app = Celery('proj')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


class MyTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

    def debug_task(self):
        logger.debug('Request: {0!r}'.format(self.request))


# http://loose-bits.com/2010/10/distributed-task-locking-in-celery.html
def only_one(function=None, key="", timeout=None, blocking=False):
    """Enforce only one celery task at a time."""

    # TODO: read parameters from settings.py
    REDIS_CLIENT = redis.StrictRedis(host='redis', port=6379, db=0)

    def _dec(run_func):
        """Decorator."""

        # With @functools.wraps applied, our function can retain its attribute
        @functools.wraps(run_func)
        def _caller(*args, **kwargs):
            """Caller."""
            ret_value = None
            have_lock = False
            lock = REDIS_CLIENT.lock(key, timeout=timeout)
            try:
                logger.debug("Acquiring lock...")
                have_lock = lock.acquire(blocking=blocking)
                if have_lock:
                    logger.debug("Calling function...")
                    ret_value = run_func(*args, **kwargs)

                else:
                    logger.warn("Lock already took by another task")

            finally:
                if have_lock:
                    logger.debug("Releasing lock")
                    lock.release()

            return ret_value

        return _caller

    return _dec(function) if function is not None else _dec


@app.task(bind=True, base=MyTask)
@only_one(key="SingleTask", timeout=60 * 5, blocking=True)
def test_single(self, arg):
    self.debug_task()
    logger.info("Received: %s" % str(arg))
    logger.info("Sleep for a minute...")
    sleep(60)
    logger.info("Done")
    return "success"


@app.task(bind=True, base=MyTask)
def test(self, arg):
    self.debug_task()
    logger.info("Received: %s" % str(arg))
    logger.info("Sleep for a minute...")
    sleep(60)
    logger.info("Done")
    return "success"


# https://stackoverflow.com/a/51429597
@app.task(bind=True, base=MyTask)
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


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=12, minute=0),
        clearsessions.s(),
    )
