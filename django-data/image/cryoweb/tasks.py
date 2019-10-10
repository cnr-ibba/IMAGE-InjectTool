#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 11:33:09 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Inspired from

http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html

"""

from celery.utils.log import get_task_logger

from common.tasks import BaseTask, exclusive_task
from image.celery import app as celery_app
from submissions.tasks import ImportGenericTaskMixin

from .helpers import cryoweb_import, upload_cryoweb
from .models import truncate_database

# get a logger for tasks
logger = get_task_logger(__name__)


# clean cryoweb database after calling decorated function
def clean_cryoweb_database(f):
    logger.debug("Decorating %s" % (f))

    def wrap(*args, **kwargs):
        result = f(*args, **kwargs)

        # cleaning up database without knowing if load is successful or not
        logger.info("Cleaning up cryoweb database")
        truncate_database()

        return result

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__

    # return decorated function
    return wrap


class ImportCryowebTask(ImportGenericTaskMixin, BaseTask):
    """
    An exclusive task wich upload a *data-only* cryoweb dump in cryoweb
    database and then fill up :ref:`UID <The Unified Internal Database>`
    tables. After data import (wich could be successful or not) cryoweb
    helper database is cleanded and restored in the original status::

        from cryoweb.tasks import ImportCryowebTask

        # call task asynchronously
        task = ImportCryowebTask()
        res = task.delay(submission_id)

    Args:
        submission_id (int): the submission primary key

    Returns:
        str: a message string (ex. success)
    """

    name = "Import Cryoweb"
    description = """Import Cryoweb data from Cryoweb dump"""
    action = "cryoweb import"

    # decorate function in order to cleanup cryoweb database after data import
    @exclusive_task(
            task_name="Import Cryoweb",
            lock_id="ImportFromCryoWeb",
            blocking=True)
    def run(self, submission_id):
        return super().run(submission_id)

    @clean_cryoweb_database
    def import_data_from_file(self, submission_obj):
        """Call the custom import method"""

        # upload data into cryoweb database
        status = upload_cryoweb(submission_obj.id)

        # if something went wrong, uploaded_cryoweb has token the exception
        # ad update submission.message field
        if status is False:
            return status

        # load cryoweb data into UID
        # check status
        status = cryoweb_import(submission_obj)

        return status


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ImportCryowebTask)
