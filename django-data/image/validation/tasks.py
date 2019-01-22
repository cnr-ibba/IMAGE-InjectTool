#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:22:33 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Useful staff to deal with validation process

"""

from time import sleep

from celery import task
from celery.utils.log import get_task_logger

from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Sample, Animal, STATUSES

# Get an instance of a logger
logger = get_task_logger(__name__)

# get available statuses
READY = STATUSES.get_value('ready')
ERROR = STATUSES.get_value('error')
NEED_REVISION = STATUSES.get_value('need_revision')


class ValidateTask(MyTask):
    name = "Validate Submission"
    description = """Validate submission data against IMAGE rules"""

    # define my class attributes
    def __init__(self, *args, **kwargs):
        super(ValidateTask, self).__init__(*args, **kwargs)

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        self.submission_obj.status = ERROR
        self.submission_obj.message = (
            "Error in IMAGE Validation: %s" % str(exc))
        self.submission_obj.save()

        # send a mail to the user with the stacktrace (einfo)
        self.submission_obj.owner.email_user(
            "Error in IMAGE Validation %s" % (self.submission_id),
            ("Something goes wrong with validation. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

    # TODO: define a method to inform user for error in validation (Task run
    # with success)

    def run(self, submission_id):
        """This function is called when delay is called"""

        # assign my submission id
        self.submission_id = submission_id

        # call innner merthod and return results
        return self.validate_submission()

    def validate_submission(self):
        """a function to perform validation steps"""

        logger.info("validate_submission started")

        # get submissio object
        submission = Submission.objects.get(pk=self.submission_id)

        # TODO: do stuff
        sleep(10)

        for sample in Sample.objects.filter(name__submission=submission):
            logger.debug("Validating %s" % (sample))
            # TODO: test against sample
            sample.name.status = READY
            sample.name.save()

        for animal in Animal.objects.filter(name__submission=submission):
            logger.debug("Validating %s" % (animal))
            # TODO: test agains animal
            animal.name.status = READY
            animal.name.save()

        # Update submission status
        # TODO: set a proper value for status (READY or NEED_REVISION)
        submission.status = READY
        submission.message = "Submission validated with success"
        submission.save()

        logger.info("validate_submission completed")

        return "success"


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ValidateTask)
