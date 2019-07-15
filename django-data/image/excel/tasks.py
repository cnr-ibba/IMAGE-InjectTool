#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 11:50:39 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from image.celery import app as celery_app, MyTask
from image_app.models import Submission
from submissions.tasks import ImportGenericTaskMixin

from .helpers import upload_template

# Get an instance of a logger
logger = get_task_logger(__name__)


class ImportTemplateTask(ImportGenericTaskMixin, MyTask):
    name = "Import Template"
    description = """Import Template data from Excel file"""
    submission_model = Submission
    datasource_type = "Template"

    def import_data_from_file(self, submission_obj):
        """Call the custom import method"""

        return upload_template(submission_obj)


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ImportTemplateTask)
