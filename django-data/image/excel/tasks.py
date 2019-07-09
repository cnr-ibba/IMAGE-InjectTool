#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 11:50:39 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger
import asyncio

from common.constants import ERROR, STATUSES
from common.helpers import send_message_to_websocket
from image.celery import app as celery_app, MyTask
from image_app.models import Submission

from .helpers import upload_template

# Get an instance of a logger
logger = get_task_logger(__name__)


class ImportTemplateTask(MyTask):
    name = "Import Template"
    description = """Import Template data from Excel file"""

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # get submissio object
        submission_obj = Submission.objects.get(pk=args[0])

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = ("Error in Template loading: %s" % (str(exc)))
        submission_obj.save()

        asyncio.get_event_loop().run_until_complete(
            send_message_to_websocket(
                {
                    'message': STATUSES.get_value_display(ERROR),
                    'notification_message': submission_obj.message
                },
                args[0]
            )
        )

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in Template loading: %s" % (args[0]),
            ("Something goes wrong with template loading. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin

    def run(self, submission_id):
        """a function to upload data into UID"""

        logger.info(
            "Start import from Template for submission: %s" % submission_id)

        # get a submission object
        submission = Submission.objects.get(pk=submission_id)

        # upload data into UID
        status = upload_template(submission)

        # if something went wrong, uploaded_cryoweb has token the exception
        # ad update submission.message field
        if status is False:
            message = "Error in uploading Template data"
            logger.error(message)

            # this a failure in my import, not the task itself
            return message

        else:
            message = "Template import completed for submission: %s" % (
                submission_id)

            # debug
            logger.info(message)

            # always return something
            return "success"


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ImportTemplateTask)
