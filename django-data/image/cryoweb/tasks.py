#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 11:33:09 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from time import sleep
from celery.utils.log import get_task_logger

from image.celery import app as celery_app, only_one, MyTask

logger = get_task_logger(__name__)


# Ok define a task for uploading cryoweb data in a exclusive way. Need
# submission_id as parameter
@celery_app.task(bind=True, base=MyTask)
@only_one(key="SingleTask", timeout=60 * 10, blocking=True)
def import_from_cryoweb(self, submission_id):
    logger.info("Start import from cryoweb for submission: %s" % submission_id)

    # do some stuff
    sleep(60)

    logger.info("Cryoweb import completed for submission: %s" % submission_id)
