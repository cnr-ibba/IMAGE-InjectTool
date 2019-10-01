#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:22:33 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Useful staff to deal with validation process

"""

import json
import traceback

from collections import Counter, defaultdict
from celery.utils.log import get_task_logger

from common.constants import (
    READY, ERROR, LOADED, NEED_REVISION, COMPLETED, STATUSES, KNOWN_STATUSES)
from common.helpers import send_mail_to_admins
from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Sample, Animal
from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from validation.models import ValidationSummary

from .models import ValidationResult as ValidationResultModel
from .helpers import MetaDataValidation, OntologyCacheError, RulesetError

# Get an instance of a logger
logger = get_task_logger(__name__)

# get a dictionary from status name (ie {0: 'Waiting'})
key2status = dict([x.value for x in STATUSES])


# A class to deal with validation errors
class ValidationError(Exception):
    pass


class ValidateSubmission(object):
    """
    An helper class for submission task, useful to pass parameters like
    submission data between tasks"""

    # define my class attributes
    def __init__(self, submission_obj, ruleset):
        # track submission object
        self.submission_obj = submission_obj

        # track ruleset
        self.ruleset = ruleset

        # collect all unique messages for samples and animals
        self.animals_messages = defaultdict(list)
        self.samples_messages = defaultdict(list)

        self.animals_offending_columns = dict()
        self.samples_offending_columns = dict()

        # track global statuses for animals and samples
        # Don't set keys: if you take a key which doesn't exists, you will
        # get 0 instead of key errors. This is how Counter differ from a
        # default dictionary object
        self.animals_statuses = Counter()
        self.samples_statuses = Counter()

    def check_valid_statuses(self):
        """Check if validation return with an unsupported status message"""

        # test for keys in model_statuses
        for key in self.animals_statuses.keys():
            if key not in KNOWN_STATUSES:
                logger.error("Unsupported status '%s' from validation" % key)
                return False

        for key in self.samples_statuses.keys():
            if key not in KNOWN_STATUSES:
                logger.error("Unsupported status '%s' from validation" % key)
                return False

        # if I arrive here, all validation statuses are handled
        return True

    def __has_key_in_rules(self, key):
        """Generic function to test errors in validation rules"""

        if (self.animals_statuses[key] > 0 or
                self.samples_statuses[key] > 0):
            return True

        else:
            return False

    def has_errors_in_rules(self):
        "Return True if there is any errors in validation rules"""

        return self.__has_key_in_rules('Error')

    def has_warnings_in_rules(self):
        "Return True if there is any warnings in validation rules"""

        return self.__has_key_in_rules('Warning')

    def validate_model(self, model):
        logger.debug("Validating %s" % (model))

        # thsi could be animal or sample
        if isinstance(model, Sample):
            model_statuses = self.samples_statuses

        elif isinstance(model, Animal):
            model_statuses = self.animals_statuses

        # get data in biosample format
        data = model.to_biosample()

        # input is a list object
        usi_result = self.ruleset.check_usi_structure([data])

        # if I have errors here, JSON isn't valid: this is not an error
        # on user's data but on InjectTool itself
        if usi_result.get_overall_status() != 'Pass':
            # update statuses (update counters), mark model and return
            self.update_statuses(model_statuses, model, usi_result)

            # It make no sense continue validation since JSON is wrong
            return

        # no check_duplicates: it checks against alias (that is a pk)
        # HINT: improve check_duplicates or implement database constraints

        # check against image metadata
        ruleset_result = self.ruleset.validate(data)

        # update status and track data in a overall variable
        self.update_statuses(model_statuses, model, ruleset_result)

    # inspired from validation.deal_with_validation_results
    def update_statuses(self, model_statuses, model, result):
        """
        Update validation summary counter and then mark model with an
        appropriate status (READY for Pass and Warning, NEED_REVISION for
        the remaining statuses)

        Args:
            model_statuses (Counter): a counter object for animal or sample
            validation statuese
            model (Sample/Animal): a Sample or Animal object
            result (ValidationResultRecord): a validation result for a record
        """

        # get overall status (ie Pass, Error)
        overall = result.get_overall_status()

        # set model as valid even if has some warnings
        if overall in ["Pass", "Warning"]:
            self.mark_model(model, result, READY)

        else:
            model_statuses.update(['Issues'])
            self.mark_model(model, result, NEED_REVISION)

        # update a collections.Counter objects by key
        model_statuses.update({overall})
        model_statuses.update(['Known'])

    def mark_model(self, model, result, status):
        """Set status to a model and instantiate a ValidationResult obj"""

        messages = result.get_messages()

        # get comparable messages for batch update
        comparable_messages = list()
        for result_set in result.result_set:
            comparable_messages.append({
                'message': result_set.get_comparable_str(),
                'offending_column': result_set.get_field_name()
            })
        overall_status = result.get_overall_status()

        # Save all messages for validation summary
        if isinstance(model, Sample):
            for message in comparable_messages:
                # samples_messages is a counter object
                self.samples_messages[message['message']].append(model.pk)
                self.samples_offending_columns[message['message']] = \
                    message['offending_column']

        # is as an animal object
        elif isinstance(model, Animal):
            for message in comparable_messages:
                self.animals_messages[message['message']].append(model.pk)
                self.animals_offending_columns[message['message']] = \
                    message['offending_column']

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

        # ok, don't update Name statuses for submitted objects which
        # already are in biosamples and pass validation
        if model.name.status == COMPLETED and status == READY:
            logger.debug(
                "Ignoring %s: status was '%s' and validation is OK" % (
                    model, key2status[model.name.status]))

        else:
            logger.debug(
                "Marking %s with '%s' status (%s)" % (
                    model, key2status[status], messages))

            # update model status and save
            model.name.status = status
            model.name.save()

    def create_validation_summary(self):
        """
        This function will create ValidationSummary object that will be used
        on validation_summary view
        """

        for model_type in ['animal', 'sample']:
            summary_obj, created = ValidationSummary.objects.get_or_create(
                submission=self.submission_obj, type=model_type)

            if created:
                logger.debug(
                    "Created %s validationSummary for %s" % (
                        model_type, self.submission_obj))

            # reset all_count
            summary_obj.reset_all_count()

            if model_type == 'animal':
                messages = self.animals_messages
                model_statuses = self.animals_statuses
                offending_column = self.animals_offending_columns

            # Im cycling with animal and sample type
            else:
                messages = self.samples_messages
                model_statuses = self.samples_statuses
                offending_column = self.samples_offending_columns

            summary_obj.submission = self.submission_obj

            # they are counter object, so no Keyerror and returns 0
            summary_obj.pass_count = model_statuses['Pass']
            summary_obj.warning_count = model_statuses['Warning']
            summary_obj.error_count = model_statuses['Error']
            summary_obj.issues_count = model_statuses['Issues']
            summary_obj.validation_known_count = model_statuses['Known']

            validation_messages = list()

            for message, ids in messages.items():
                validation_messages.append({
                    'message': message,
                    'count': len(ids),
                    'ids': ids,
                    'offending_column': offending_column[message]
                })

            summary_obj.messages = validation_messages
            summary_obj.type = model_type
            summary_obj.save()

        logger.debug(
            "Results for submission %s: animals - %s, samples - %s" % (
                self.submission_obj,
                dict(self.animals_statuses),
                dict(self.samples_statuses))
        )


class ValidateTask(MyTask):
    name = "Validate Submission"
    description = """Validate submission data against IMAGE rules"""

    # http://docs.celeryproject.org/en/latest/userguide/tasks.html#instantiation
    # A task is not instantiated for every request, but is registered in
    # the task registry as a global instance. This means that the __init__
    # constructor will only be called once per process, and that the
    # task class is semantically closer to an Actor. if you have a task and
    # you route every request to the same process, then it will keep state
    # between requests. This can also be useful to cache resources, For
    # example, a base Task class that caches a database connection

    # extract a generic send_message for all modules which need it
    def send_message(self, submission_obj):
        """
        Update submission.status and submission message using django
        channels

        Args:
            submission_obj (image_app.models.Submission): an UID submission
            object
        """

        send_message(
            submission_obj,
            validation_message=construct_validation_message(submission_obj))

    def __generic_error_report(
            self, submission_obj, status, message, notify_admins=False):
        """
        Generic report for updating submission objects and send email after
        an exception is called

        Args:
            submission_obj (image_app.models.Submission): an UID submission
            object
            status (int): a :py:class:`common.constants.STATUSES` object
            message (str): a text object
            notify_admins (bool): send mail to the admins or not
        """

        # mark submission with its status
        submission_obj.status = status
        submission_obj.message = message
        submission_obj.save()

        self.send_message(submission_obj)

        # get exception info
        einfo = traceback.format_exc()

        # send a mail to the user with the stacktrace (einfo)
        email_subject = "Error in IMAGE Validation: %s" % (message)
        email_message = (
            "Something goes wrong with validation. Please report "
            "this to InjectTool team\n\n %s" % str(einfo))

        submission_obj.owner.email_user(
            email_subject,
            email_message,
        )

        # this is a common.helpers method that should be used when needed
        if notify_admins:
            # submit mail to admins
            send_mail_to_admins(email_subject, email_message)

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # define message
        message = "Unknown error in validation - %s" % str(exc)

        # get submissio object
        submission_obj = Submission.objects.get(pk=args[0])

        # call generic report which update submission and send email
        self.__generic_error_report(
            submission_obj, ERROR, message, notify_admins=True)

        # returns None: this task will have the ERROR status

    # TODO: define a method to inform user for error in validation (Task run
    # with success but errors in data)

    def temporary_error_report(self, exc, submission_obj):
        """
        Deal with known issues in validation task. Notify the user using
        email and set status as READY in order to recall this task

        Args:
            exc (Exception): an py:exc`Exception` object
            submission_obj (image_app.models.Submission): an UID submission
            object

        Return
            str: "success" since this task is correctly managed
        """

        logger.error("Error in validation: %s" % exc)

        message = "Errors in EBI API endpoints. Please try again later"
        logger.error(message)

        # call generic report which update submission and send email
        self.__generic_error_report(submission_obj, LOADED, message)

        return "success"

    def ruleset_error_report(self, exc, submission_obj):
        """
        Deal with ruleset issue in validation task. Notify the user using
        email and set status as ERROR, since he can't do anything without
        admin intervention

        Args:
            exc (Exception): an py:exc`Exception` object
            submission_obj (image_app.models.Submission): an UID submission
            object

        Return
            str: "success" since this task is correctly managed
        """

        logger.error("Error ruleset: %s" % exc)

        message = (
            "Error in IMAGE-metadata ruleset. Please inform InjectTool team")
        logger.error(message)

        # call generic report which update submission and send email
        self.__generic_error_report(
            submission_obj, ERROR, message, notify_admins=True)

        return "success"

    def run(self, submission_id):
        """a function to perform validation steps"""

        logger.info("Validate Submission started")

        # get submissio object
        submission_obj = Submission.objects.get(pk=submission_id)

        # read rules when task starts. Model issues when starting
        # OntologyCache at start
        try:
            self.ruleset = MetaDataValidation()

        except OntologyCacheError as exc:
            return self.temporary_error_report(exc, submission_obj)

        except RulesetError as exc:
            return self.ruleset_error_report(exc, submission_obj)

        # get a submission data helper instance
        validate_submission = ValidateSubmission(submission_obj, self.ruleset)

        try:
            for animal in Animal.objects.filter(
                    name__submission=submission_obj).order_by('id'):
                validate_submission.validate_model(animal)

            for sample in Sample.objects.filter(
                    name__submission=submission_obj).order_by('id'):
                validate_submission.validate_model(sample)

        # TODO: errors in validation should raise custom exception
        except json.decoder.JSONDecodeError as exc:
            return self.temporary_error_report(exc, submission_obj)

        except Exception as exc:
            raise self.retry(exc=exc)

        # if error messages changes in IMAGE-ValidationTool, all this
        # stuff isn't valid and I throw an exception

        if not validate_submission.check_valid_statuses():
            message = (
                "Unsupported validation status for submission %s" % (
                    submission_obj))

            # debug: print error in log
            logger.error(message)

            # create validation summary
            validate_submission.create_validation_summary()

            # mark submission with ERROR (this is not related to user data)
            # calling the appropriate method passing ERROR as status
            self.submission_fail(submission_obj, message, status=ERROR)

            # raise an exception since is an InjectTool issue
            raise ValidationError(message)

        # set a proper value for status (READY or NEED_REVISION)
        # If I will found any error or warning, I will
        # return a message and I will set NEED_REVISION
        elif validate_submission.has_errors_in_rules():
            # create validation summary
            validate_submission.create_validation_summary()

            message = (
                "Error in metadata. Need revisions before submit")

            # mark submission with NEED_REVISION
            self.submission_fail(submission_obj, message)

            logger.warning(
                "Error in metadata for submission %s" % (submission_obj))

        # WOW: I can submit those data
        elif validate_submission.has_warnings_in_rules():
            # create validation summary
            validate_submission.create_validation_summary()

            message = "Submission validated with some warnings"

            # mark submission with READY status
            self.submission_ready(submission_obj, message)

            logger.info(
                "Submission %s validated with some warning" % (submission_obj))

        else:
            # create validation summary
            validate_submission.create_validation_summary()

            message = "Submission validated with success"

            # mark submission with READY status
            self.submission_ready(submission_obj, message)

            logger.info(
                "Submission %s validated with success" % (submission_obj))

        logger.info("Validate Submission completed")

        return "success"

    def __mark_submission(self, submission_obj, message, status):
        """Mark submission with status and message"""

        submission_obj.status = status
        submission_obj.message = message
        submission_obj.save()

        self.send_message(submission_obj)

    def submission_fail(self, submission_obj, message, status=NEED_REVISION):
        """Mark a submission with NEED_REVISION status"""

        # ovverride message
        message = ("Validation got errors: %s" % (message))
        self.__mark_submission(submission_obj, message, status)

    def submission_ready(self, submission_obj, message):
        """Mark a submission with READY status"""

        self.__mark_submission(submission_obj, message, READY)


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ValidateTask)
