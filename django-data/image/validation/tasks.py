#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:22:33 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Useful staff to deal with validation process

"""

import json
import traceback
import asyncio

from collections import Counter
from celery.utils.log import get_task_logger

from django.conf import settings
from django.core.mail import send_mass_mail
from django.core.exceptions import ObjectDoesNotExist

from common.constants import (
    READY, ERROR, LOADED, NEED_REVISION, COMPLETED, STATUSES)
from common.helpers import send_message_to_websocket
from validation.helpers import construct_validation_message
from image.celery import app as celery_app, MyTask
from image_app.helpers import get_admin_emails
from image_app.models import Submission, Sample, Animal
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

    def send_message(self, status, submission_obj):
        """
        Update submission.status and submission message using django
        channels

        Args:
            status (int): a :py:class:`common.constants.STATUSES` object
            submission_obj (image_app.models.Submission): an UID submission
            object
        """

        asyncio.get_event_loop().run_until_complete(
            send_message_to_websocket(
                {
                    'message': STATUSES.get_value_display(status),
                    'notification_message': submission_obj.message,
                    'validation_message': construct_validation_message(
                            submission_obj)
                },
                submission_obj.pk
            )
        )

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

        self.send_message(status, submission_obj)

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

        if notify_admins:
            # submit mail to admins
            datatuple = (
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                get_admin_emails())

            send_mass_mail((datatuple, ))

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

        # collect all unique messages for samples and animals
        self.messages_samples = dict()
        self.messages_animals = dict()

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

        # track global statuses for animals and samples
        submission_statuses_animals = Counter(
            {'Pass': 0,
             'Warning': 0,
             'Error': 0,
             'JSON': 0})

        submission_statuses_samples = Counter(
            {'Pass': 0,
             'Warning': 0,
             'Error': 0,
             'JSON': 0})

        try:
            for animal in Animal.objects.filter(
                    name__submission=submission_obj).order_by('id'):
                self.validate_model(animal, submission_statuses_animals)

            for sample in Sample.objects.filter(
                    name__submission=submission_obj).order_by('id'):
                self.validate_model(sample, submission_statuses_samples)

        # TODO: errors in validation should raise custom exception
        except json.decoder.JSONDecodeError as exc:
            return self.temporary_error_report(exc, submission_obj)

        except Exception as exc:
            raise self.retry(exc=exc)

        # test for keys in submission_statuses
        statuses_animals = sorted(submission_statuses_animals.keys())
        statuses_samples = sorted(submission_statuses_samples.keys())

        # if error messages changes in IMAGE-ValidationTool, all this
        # stuff isn't valid and I throw an exception
        if statuses_animals != ['Error', 'JSON', 'Pass', 'Warning'] or \
                statuses_samples != ['Error', 'JSON', 'Pass', 'Warning']:
            message = "Error in statuses for submission %s: animals - %s, " \
                      "samples - %s" % (submission_obj, statuses_animals,
                                        statuses_samples)

            # debug: print error in log
            logger.error(message)

            # mark submission with ERROR (this is not related to user data)
            # calling the appropriate method passing ERROR as status
            self.submission_fail(submission_obj, message, status=ERROR)

            # raise an exception since is an InjectTool issue
            raise ValidationError(message)

        # If I have any error in JSON is a problem of injectool
        if self.has_errors_in_json(submission_statuses_animals) or \
                self.has_errors_in_json(submission_statuses_samples):
            # mark submission with NEED_REVISION
            self.submission_fail(submission_obj, "Wrong JSON structure")
            self.create_validation_summary(submission_obj,
                                           submission_statuses_animals,
                                           submission_statuses_samples)

            # debug
            logger.warning(
                "Wrong JSON structure for submission %s" % (submission_obj))

            logger.debug(
                "Results for submission %s: animals - %s, samples - %s" % (
                    submission_id, submission_statuses_animals,
                    submission_statuses_samples)
            )

        # set a proper value for status (READY or NEED_REVISION)
        # If I will found any error or warning, I will
        # return a message and I will set NEED_REVISION
        elif self.has_errors_in_rules(submission_statuses_animals) or \
                self.has_errors_in_rules(submission_statuses_samples):
            message = (
                "Error in metadata. Need revisions before submit")

            # mark submission with NEED_REVISION
            self.submission_fail(submission_obj, message)
            self.create_validation_summary(submission_obj,
                                           submission_statuses_animals,
                                           submission_statuses_samples)

            logger.warning(
                "Error in metadata for submission %s" % (submission_obj))

            logger.debug(
                "Results for submission %s: animals - %s, samples - %s" % (
                    submission_id, submission_statuses_animals,
                    submission_statuses_samples)
            )

        # WOW: I can submit those data
        elif self.has_warnings_in_rules(submission_statuses_animals) or \
                self.has_warnings_in_rules(submission_statuses_samples):
            submission_obj.status = READY
            submission_obj.message = "Submission validated with some warnings"
            submission_obj.save()
            self.create_validation_summary(submission_obj,
                                           submission_statuses_animals,
                                           submission_statuses_samples)

            # send message with channel
            self.send_message(READY, submission_obj)

            logger.info(
                "Submission %s validated with some warning" % (submission_obj))

            logger.debug(
                "Results for submission %s: animals - %s, samples - %s" % (
                    submission_id, submission_statuses_animals,
                    submission_statuses_samples)
            )

        else:
            submission_obj.status = READY
            submission_obj.message = "Submission validated with success"
            submission_obj.save()
            self.create_validation_summary(submission_obj,
                                           submission_statuses_animals,
                                           submission_statuses_samples)

            # send message with channel
            self.send_message(READY, submission_obj)

            logger.info(
                "Submission %s validated with success" % (submission_obj))

            logger.debug(
                "Results for submission %s: animals - %s, samples - %s" % (
                    submission_id, submission_statuses_animals,
                    submission_statuses_samples)
            )

        logger.info("Validate Submission completed")

        return "success"

    def validate_model(self, model, submission_statuses):
        logger.debug("Validating %s" % (model))

        # get data in biosample format
        data = model.to_biosample()

        # input is a list object
        usi_result = self.ruleset.check_usi_structure([data])

        # if I have errors here, JSON isn't valid: this is not an error
        # on user's data but on InjectTool itself
        if len(usi_result) > 0:
            # update counter for JSON
            submission_statuses.update({'JSON': len(usi_result)})

            # update model results
            self.mark_model(model, usi_result, NEED_REVISION)

            # It make no sense continue validation since JSON is wrong
            return

        # no check_duplicates: it checks against alias (that is a pk)
        # HINT: improve check_duplicates or implement database constraints

        # check against image metadata
        ruleset_result = self.ruleset.validate(data)

        # update status and track data in a overall variable
        self.update_statuses(submission_statuses, model, ruleset_result)

    # inspired from validation.deal_with_validation_results
    def update_statuses(self, submission_statuses, model, result):
        # get overall status (ie Pass, Error)
        overall = result.get_overall_status()

        # set model as valid even if has some warnings
        if overall in ["Pass", "Warning"]:
            self.mark_model(model, result, READY)

        else:
            self.mark_model(model, result, NEED_REVISION)

        # update a collections.Counter objects by key
        submission_statuses.update({overall})

    def has_errors_in_rules(self, submission_statuses):
        "Return True if there is any errors"""

        if submission_statuses["Error"] != 0:
            return True
        else:
            return False

    def has_warnings_in_rules(self, submission_statuses):
        "Return True if there is any warnings"""

        if submission_statuses["Warning"] != 0:
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
            comparable_messages = result
            overall_status = "Wrong JSON structure"

        else:
            messages = result.get_messages()
            # get comparable messages for batch update
            comparable_messages = list()
            for result_set in result.result_set:
                comparable_messages.append(result_set.get_comparable_str())
            overall_status = result.get_overall_status()

        # Save all messages for validation summary
        if isinstance(model, Sample):
            # messages_samples might not exist when doing tests
            if not hasattr(self, 'messages_samples'):
                self.messages_samples = dict()
            for message in comparable_messages:
                self.messages_samples.setdefault(message, 0)
                self.messages_samples[message] += 1
        elif isinstance(model, Animal):
            # messages_animals might not exist when doing tests
            if not hasattr(self, 'messages_animals'):
                self.messages_animals = dict()
            for message in comparable_messages:
                self.messages_animals.setdefault(message, 0)
                self.messages_animals[message] += 1

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

    def submission_fail(self, submission_obj, message, status=NEED_REVISION):
        """Mark a submission with NEED_REVISION status"""

        submission_obj.status = status
        submission_obj.message = ("Validation got errors: %s" % (message))
        submission_obj.save()
        self.send_message(status, submission_obj)

    def create_validation_summary(self, submission_obj,
                                  submission_statuses_animals,
                                  submission_statuses_samples):
        """
        This function will create ValidationSummary object that will be used
        on validation_summary view
        Args:
            submission_obj: submission ref which has gone through validation
            submission_statuses_animals: Counter with statuses for animals
            submission_statuses_samples: Counter with statuses for samples
        """
        for model_type in ['animal', 'sample']:
            try:
                validation_summary = submission_obj.validationsummary_set.get(
                    type=model_type
                )
            except ObjectDoesNotExist:
                validation_summary = ValidationSummary()
            if model_type == 'animal':
                messages = self.messages_animals
                submission_statuses = submission_statuses_animals
            elif model_type == 'sample':
                messages = self.messages_samples
                submission_statuses = submission_statuses_samples
            else:
                messages = dict()
                submission_statuses = dict()
            validation_summary.submission = submission_obj
            validation_summary.pass_count = submission_statuses.get('Pass', 0)
            validation_summary.warning_count = submission_statuses.get(
                'Warning', 0)
            validation_summary.error_count = submission_statuses.get(
                'Error', 0)
            validation_summary.json_count = submission_statuses.get('JSON', 0)
            validation_messages = list()
            for message, count in messages.items():
                validation_messages.append({
                    'message': message,
                    'count': count
                })
            validation_summary.messages = validation_messages
            validation_summary.type = model_type
            validation_summary.save()


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(ValidateTask)
