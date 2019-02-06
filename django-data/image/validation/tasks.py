#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:22:33 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Useful staff to deal with validation process

"""

import json
import traceback

from collections import Counter
from celery.utils.log import get_task_logger

from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Sample, Animal, STATUSES

from .helpers import validation
from .constants import IMAGE_RULESET
from .models import ValidationResult as ValidationResultModel

# Get an instance of a logger
logger = get_task_logger(__name__)

# get available statuses
READY = STATUSES.get_value('ready')
ERROR = STATUSES.get_value('error')
NEED_REVISION = STATUSES.get_value('need_revision')

# get a dictionary from status name (ie {0: 'Waiting'})
key2status = dict([x.value for x in STATUSES])


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

        # get submissio object
        submission_obj = Submission.objects.get(pk=args[0])

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = ("Error in IMAGE Validation: %s" % (str(exc)))
        submission_obj.save()

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in IMAGE Validation: %s" % (args[0]),
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
        submission_obj = Submission.objects.get(pk=submission_id)

        # track global statuses
        submission_statuses = Counter(
            {'Pass': 0,
             'Warning': 0,
             'Error': 0,
             'JSON': 0})

        try:
            for animal in Animal.objects.filter(
                    name__submission=submission_obj):
                self.validate_model(animal, submission_statuses)

            for sample in Sample.objects.filter(
                    name__submission=submission_obj):
                self.validate_model(sample, submission_statuses)

        # TODO: errors in validation shuold raise custom exception
        except json.decoder.JSONDecodeError as exc:
            logger.error("Error in validation: %s" % exc)

            message = "Errors in EBI API endpoints. Please try again later"
            logger.error(message)

            # mark submission with NEED_REVISION
            self.submission_fail(submission_obj, message)

            # get exception info
            einfo = traceback.format_exc()

            # send a mail to the user with the stacktrace (einfo)
            submission_obj.owner.email_user(
                "Error in IMAGE Validation: %s" % (message),
                ("Something goes wrong with validation. Please report "
                 "this to InjectTool team\n\n %s" % str(einfo)),
            )

            return "success"

        except Exception as exc:
            raise self.retry(exc=exc)

        # test for keys in submission_statuses
        statuses = sorted(submission_statuses.keys())

        # if error messages changes in IMAGE-ValidationTool, all this
        # stuff isn't valid and I throw an exception
        if statuses != ['Error', 'JSON', 'Pass', 'Warning']:
            message = "Error in statuses for submission %s: %s" % (
                submission_obj, statuses)

            # debug: print error in log
            logger.error(message)

            # mark submission with ERROR (this is not related to user data)
            # calling the appropriate method passing ERROR as status
            self.submission_fail(submission_obj, message, status=ERROR)

            # raise an exception since is an InjectTool issue
            raise ValidationError(message)

        # If I have any error in JSON is a problem of injectool
        if self.has_errors_in_json(submission_statuses):
            # mark submission with NEED_REVISION
            self.submission_fail(submission_obj, "Wrong JSON structure")

            # debug
            logger.warning(
                "Wrong JSON structure for submission %s" % (submission_obj))

            logger.debug("Results for submission %s: %s" % (
                submission_id, submission_statuses))

        # set a proper value for status (READY or NEED_REVISION)
        # If I will found any error or warning, I will
        # return a message and I will set NEED_REVISION
        elif self.has_errors_in_rules(submission_statuses):
            message = (
                "Error in metadata rules. Need revisions before submit")

            # mark submission with NEED_REVISION
            self.submission_fail(submission_obj, message)

            logger.warning(
                "Error in metadata rules for submission %s" % (submission_obj))

            logger.debug("Results for submission %s: %s" % (
                submission_id, submission_statuses))

        # WOW: I can submit those data
        else:
            submission_obj.status = READY
            submission_obj.message = "Submission validated with success"
            submission_obj.save()

            logger.info(
                "Submission %s validated with success" % (submission_obj))

            logger.debug("Results for submission %s: %s" % (
                submission_id, submission_statuses))

        logger.info("Validate Submission completed")

        return "success"

    def validate_model(self, model, submission_statuses):
        logger.debug("Validating %s" % (model))

        # get data in biosample format
        data = model.to_biosample()

        # input is a list object
        usi_result = validation.check_usi_structure([data])

        # if I have errors here, JSON isn't valid: this is not an error
        # on user's data but on InjectTool itself
        if len(usi_result) > 0:
            # update counter for JSON
            submission_statuses.update({'JSON': len(usi_result)})

            # update model results
            self.mark_model(model, usi_result, NEED_REVISION)

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
            self.mark_model(model, result, NEED_REVISION)

        else:
            self.mark_model(model, result, READY)

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

    def mark_model(self, model, result, status):
        """Set status to a model and instantiate a ValidationResult obj"""

        if isinstance(result, list):
            messages = result
            overall_status = "Wrong JSON structure"

        else:
            messages = result.get_messages()
            overall_status = result.get_overall_status()

        logger.debug(
            "Marking %s with '%s' status (%s)" % (
                model, key2status[status], messages))

        # get a validation result model or create a new one
        if hasattr(model.name, 'validationresult'):
            validationresult = model.name.validationresult
        else:
            validationresult = ValidationResultModel()
            model.name.validationresult = validationresult

        # setting valdiationtool results and save
        validationresult.messages = messages
        validationresult.status = overall_status
        validationresult.save()

        # update model status and save
        model.name.status = status
        model.name.save()

    def submission_fail(self, submission_obj, message, status=NEED_REVISION):
        """Mark a submission with NEED_REVISION status"""

        submission_obj.status = status
        submission_obj.message = ("Validation got errors: %s" % (message))
        submission_obj.save()


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ValidateTask)
