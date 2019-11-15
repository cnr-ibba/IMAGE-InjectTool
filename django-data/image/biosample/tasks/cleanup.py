#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 16:06:10 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

from datetime import timedelta
from celery.utils.log import get_task_logger
from django.utils import timezone

from common.constants import COMPLETED
from common.tasks import BaseTask, NotifyAdminTaskMixin, exclusive_task
from image.celery import app as celery_app

from ..models import Submission

# Get an instance of a logger
logger = get_task_logger(__name__)


class CleanUpTask(NotifyAdminTaskMixin, BaseTask):
    """Perform biosample.models cleanup by selecting old completed submission
    and remove them from database"""

    name = "Clean biosample models"
    description = """Clean biosample models"""

    @exclusive_task(task_name="Clean biosample models", lock_id="CleanUpTask")
    def run(self):
        """
        This function is called when delay is called. It will acquire a lock
        in redis, so those tasks are mutually exclusive

        Returns:
            str: success if everything is ok. Different messages if task is
            already running or exception is caught"""

        logger.info("Clean biosample.database started")

        # get an interval starting from 7 days from now
        interval = timezone.now() - timedelta(days=7)

        # select all COMPLETED object older than interval
        qs = Submission.objects.filter(
            updated_at__lt=interval,
            status=COMPLETED)

        logger.info(
            "Deleting %s biosample.models.Submission objects" % qs.count())

        # delete all old objects
        qs.delete()

        # debug
        logger.info("Clean biosample.database completed")

        return "success"


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(CleanUpTask)
