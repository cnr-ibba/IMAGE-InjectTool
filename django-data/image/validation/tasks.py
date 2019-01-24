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


# A class to deal with validation errors
class ValidationError(Exception):
    pass


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

        # mark submission with ERROR
        submission_obj = self.submission_fail(
            args[0], str(exc))

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in IMAGE Validation %s" % (args[0]),
            ("Something goes wrong with validation. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin

    # TODO: define a method to inform user for error in validation (Task run
    # with success but errors in data)

    def run(self, submission_id):
        """a function to perform validation steps"""

        logger.info("Validate Submission started")

        # get submissio object
        submission = Submission.objects.get(pk=submission_id)

        # track global statuses
        submission_statuses = Counter(
            {'Pass': 0,
             'Warning': 0,
             'Error': 0,
             'JSON': 0})

        for animal in Animal.objects.filter(name__submission=submission):
            self.validate_model(animal, submission_statuses)

        for sample in Sample.objects.filter(name__submission=submission):
            self.validate_model(sample, submission_statuses)

        # test for keys in submission_statuses
        statuses = sorted(submission_statuses.keys())

        # if error messages changes in IMAGE-ValidationTool, all this
        # stuff isn't valid and I throw an exception
        if statuses != ['Error', 'JSON', 'Pass', 'Warning']:
            # mark submission with ERROR
            self.submission_fail(
                submission_id, "Error in submission statuses: %s" % (
                    statuses))

            raise ValidationError("Error in submission statuses: %s" % (
                    statuses))

        # If I have any error in JSON is a problem of injectool
        if self.has_errors_in_json(submission_statuses):
            logger.error("Results for submission %s: %s" % (
                submission_id, submission_statuses))

            # mark submission with ERROR
            self.submission_fail(
                submission_id, "Validation got errors: Wrong JSON structure")

            # raise an exception
            raise ValidationError(
                "Validation got errors: Wrong JSON structure")

        # set a proper value for status (READY or NEED_REVISION)
        # If I will found any error or warning, I will
        # return a message and I will set NEED_REVISION
        elif self.has_errors_in_rules(submission_statuses):
            submission.status = NEED_REVISION
            submission.message = (
                "Validation got errors: need revisions before submit")
            submission.save()

            logger.warning("Results for submission %s: %s" % (
                submission_id, submission_statuses))

        # WOW: I can submit those data
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

        # if I have errors here, JSON isn't valid: this is not an error
        # on user's data but on InjectTool itself
        if len(usi_results) > 0:
            # update counter for JSON
            submission_statuses.update({'JSON': len(usi_results)})

            # usi_results is a list of string
            model.name.status = ERROR
            model.name.save()

            # TODO: set messages for name

            # It make no sense check_with_ruleset, since JSON is wrong
            return

        # no check_duplicates: it checks against alias (that is a pk)
        # HINT: improve check_duplicates or implement database constraints

        # check against image metadata
        ruleset_results = validation.check_with_ruleset([data], self.rules)

        # update status and track data in a overall variable
        self.update_statuses(submission_statuses, model, ruleset_results)

    # inspired from validation.deal_with_validation_results
    def update_statuses(self, submission_statuses, model, results):
        if len(results) != 1:
            raise ValidationError(
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

    def has_errors_in_rules(self, submission_statuses):
        "Return True if there is any error or warning"""

        if (submission_statuses["Warning"] != 0 or
                submission_statuses["Error"] != 0):
            return True
        else:
            return False

    def has_errors_in_json(self, submission_statuses):
        "Return True if there is any error in JSON"""

        return submission_statuses["JSON"] > 0

    def model_fail(self, model, messages):
        """Mark a model with NEED_REVISION status"""

        logger.debug("Model %s need to be revised: %s" % (model, messages))

        # set a proper value for status (READY or NEED_REVISION)
        model.name.status = NEED_REVISION
        model.name.save()

        # TODO: set messages for name

    def submission_fail(self, submission_id, message):
        """Mark a submission with ERROR status"""

        submission_obj = Submission.objects.get(pk=submission_id)

        submission_obj.status = ERROR
        submission_obj.message = (
            "Error in IMAGE Validation: %s" % message)
        submission_obj.save()

        return submission_obj


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ValidateTask)
