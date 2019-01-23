#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:22:33 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Useful staff to deal with validation process

"""

from collections import Counter
from celery.utils.log import get_task_logger

from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Sample, Animal, STATUSES

from .helpers import validation
from .constants import IMAGE_RULESET

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
        # http://docs.celeryproject.org/en/latest/userguide/tasks.html#instantiation
        # A task is not instantiated for every request, but is registered in
        # the task registry as a global instance. This means that the __init__
        # constructor will only be called once per process, and that the
        # task class is semantically closer to an Actor. if you have a task and
        # you route every request to the same process, then it will keep state
        # between requests. This can also be useful to cache resources, For
        # example, a base Task class that caches a database connection
        super(ValidateTask, self).__init__(*args, **kwargs)

        # read rules ONCE
        self.rules = validation.read_in_ruleset(IMAGE_RULESET)

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
    # with success but errors in data)

    def run(self, submission_id):
        """a function to perform validation steps"""

        logger.info("Validate Submission started")

        # get submissio object
        submission = Submission.objects.get(pk=submission_id)

        # track global statuses
        submission_statuses = Counter({'Pass': 0, 'Warning': 0, 'Error': 0})

        for animal in Animal.objects.filter(name__submission=submission):
            self.validate_model(animal, submission_statuses)

        for sample in Sample.objects.filter(name__submission=submission):
            self.validate_model(sample, submission_statuses)

        # set a proper value for status (READY or NEED_REVISION)
        # If I will found any error or warning, I will
        # return a message and I will set NEED_REVISION
        if self.has_errors(submission_statuses):
            submission.status = NEED_REVISION
            submission.message = (
                "Validation got errors: need revisions before submit")
            submission.save()

            logger.warning("Results for submission %s: %s" % (
                submission_id, submission_statuses))

        else:
            submission.status = READY
            submission.message = "Submission validated with success"
            submission.save()

            logger.info("Results for submission %s: %s" % (
                submission_id, submission_statuses))

        logger.info("Validate Submission completed")

        return "success"

    def validate_model(self, model, submission_statuses):
        logger.debug("Validating %s" % (model))

        # get data in biosample format
        data = model.to_biosample()

        # input is a list object
        usi_results = validation.check_usi_structure([data])

        # no check_duplicates: it checks against alias (that is a pk)
        # HINT: improve check_duplicates or implement database constraints

        # check against image metadata
        ruleset_results = validation.check_with_ruleset([data], self.rules)

        # update status and track data in a overall variable
        self.update_statuses(submission_statuses, model, ruleset_results)

        # if usi_results failed, this object is failed
        if len(usi_results) > 0:
            self.model_fail(model, usi_results[0].get_messages())

    # inspired from validation.deal_with_validation_results
    def update_statuses(self, submission_statuses, model, results):
        if len(results) != 1:
            raise Exception(
                "Number of validation results are different from expectations")

        # The hypotesys is that results is a list of one element
        result = results[0]

        # get overall status (ie Pass, Error)
        overall = result.get_overall_status()

        if overall != "Pass":
            self.model_fail(model, result.get_messages())

        else:
            # ok, I passed my validation
            model.name.status = READY
            model.name.save()

        # update a collections.Counter objects by key
        submission_statuses.update({overall})

    def has_errors(self, submission_statuses):
        "Return True if there is any error or warning"""

        if (submission_statuses["Warning"] != 0 or
                submission_statuses["Error"] != 0):
            return True
        else:
            return False

    def model_fail(self, model, messages):
        # set a proper value for status (READY or NEED_REVISION)
        model.name.status = NEED_REVISION
        model.name.save()

        # TODO: set messages for name


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ValidateTask)
