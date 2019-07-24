#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:37 2019
@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from common.constants import ERROR, NEED_REVISION
from image.celery import app as celery_app, MyTask
from image_app.models import Submission
from submissions.helpers import send_message
from validation.helpers import construct_validation_message

# Get an instance of a logger
logger = get_task_logger(__name__)


class BatchDeleteSamples(MyTask):
    name = "Batch delete samples"
    description = """Batch remove samples"""

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # get submission object
        submission_obj = Submission.objects.get(pk=args[0])

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = ("Error in batch delete for samples: %s"
                                  % (str(exc)))
        submission_obj.save()

        send_message(submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in batch delete for samples: %s" % (args[0]),
            ("Something goes wrong in batch delete for samples. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin

    def run(self, submission_id, sample_ids):
        """Function for batch update attribute in animals
        Args:
            submission_id (int): id of submission
            sample_ids (set): set with ids to delete
        """

        logger.info("Start batch delete for samples")
        # Update submission
        submission_obj = Submission.objects.get(pk=submission_id)
        submission_obj.status = NEED_REVISION
        submission_obj.message = "Data updated, try to rerun validation"
        submission_obj.save()

        send_message(
            submission_obj, construct_validation_message(submission_obj)
        )

        return 'success'


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(BatchDeleteSamples)