#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 11 14:34:27 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os

from celery import Celery, Task
from celery.utils.log import get_task_logger
from celery.signals import setup_logging

from django.core import management
from django.conf import settings


logger = get_task_logger(__name__)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image.settings')

app = Celery('proj')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


# configure logging
# https://groups.google.com/forum/#!topic/celery-users/mhcwubJTTnw
@setup_logging.connect
def configure_logging(sender=None, **kwargs):
    import logging
    import logging.config
    logging.config.dictConfig(settings.LOGGING)


class MyTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

    def debug_task(self):
        logger.debug('Request: {0!r}'.format(self.request))


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
