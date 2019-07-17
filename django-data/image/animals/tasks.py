#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:37 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from common.constants import ERROR
from common.tasks import BatchUpdateMixin
from image.celery import app as celery_app, MyTask
from image_app.models import Submission
from submissions.helpers import send_message

# Get an instance of a logger
logger = get_task_logger(__name__)


class BatchUpdateAnimals(MyTask, BatchUpdateMixin):
    name = "Batch update animals"
    description = """Batch update of field in animals"""

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # get submission object
        submission_obj = Submission.objects.get(pk=args[0])

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = ("Error in batch update for animals: %s"
                                  % (str(exc)))
        submission_obj.save()

        send_message(submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in batch update for animals: %s" % (args[0]),
            ("Something goes wrong  in batch update for animals. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin

    def run(self, submission_id, animal_ids, attribute):
        """Function for batch update attribute in animals
        Args:
            submission_id (int): id of submission
            animal_ids (dict): dict with id and values to update
            attribute (str): attribute to update
        """

        logger.info("Start batch update for animals")
        super(BatchUpdateAnimals, self).batch_update(submission_id, animal_ids,
                                                     attribute, 'animal')
        return 'success'


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(BatchUpdateAnimals)
