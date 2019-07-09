#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:37 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from image.celery import app as celery_app, MyTask
from image_app.models import Submission
from submissions.tasks import ImportGenericTaskMixin

from .helpers import upload_crbanim

# Get an instance of a logger
logger = get_task_logger(__name__)


class ImportCRBAnimTask(ImportGenericTaskMixin, MyTask):
    name = "Import CRBAnim"
    description = """Import CRBAnim data from CRBAnim data file"""
    submission_model = Submission
    datasource_type = "CRBAnim"

    def import_data_from_file(self, submission_obj):
        """Call the custom import method"""

        return upload_crbanim(submission_obj)


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ImportCRBAnimTask)
