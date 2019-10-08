#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 16:10:06 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from common.constants import ERROR
from common.tasks import NotifyAdminTaskMixin
from image_app.models import Submission

from .helpers import send_message

# Get an instance of a logger
logger = logging.getLogger(__name__)


# HINT: should I move all this stuff into image_app module?
class SubmissionTaskMixin():
    """A mixin to extend Task to support UID Submission objects"""

    action = None
    max_body_size = 5000

    def get_uid_submission(self, submission_id):
        """Get a UID Submission instance from an id

        Args:
            submission_id (int): the submission id

        Returns:
            :py:class:`Submission`: a UID submission instance
        """

        return Submission.objects.get(pk=submission_id)

    # extract a generic send_message for all modules which need it
    def send_message(self, submission_obj):
        """
        Update submission.status and submission message using django
        channels

        Args:
            submission_obj (image_app.models.Submission): an UID submission
            object
        """

        send_message(submission_obj)

    def update_submission_status(self, submission_obj, status, message):
        """Mark submission with status, then send message"""

        submission_obj.status = status
        submission_obj.message = message
        submission_obj.save()

        # send async message
        self.send_message(submission_obj)

    def mail_to_owner(self, submission_obj, subject, body):
        # truncate message body if necessary
        if len(body) > self.max_body_size:
            body = body[:self.max_body_size] + "...[truncated]"

        submission_obj.owner.email_user(subject, body)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Override the default on_failure method"""

        # call base class
        super().on_failure(exc, task_id, args, kwargs, einfo)

        # get submission object
        if 'uid_submission_id' in kwargs:
            submission_id = kwargs['uid_submission_id']

        else:
            submission_id = args[0]
        submission_obj = self.get_uid_submission(submission_id)

        # mark submission with ERROR and send message
        self.update_submission_status(
            submission_obj,
            ERROR,
            "Error in %s: %s" % (self.action, str(exc))
        )

        # send a mail to the user with the stacktrace (einfo)
        subject = "Error in %s for submission %s" % (
            self.action, submission_id)
        body = (
            "Something goes wrong with %s. Please report "
            "this to InjectTool team\n\n %s" % (
                self.action,
                str(einfo))
        )

        self.mail_to_owner(submission_obj, subject, body)


class ImportGenericTaskMixin(SubmissionTaskMixin, NotifyAdminTaskMixin):
    """A mixing used to import datasource into UID"""

    action = None

    def run(self, submission_id):
        """a function to upload data into UID"""

        logger.info(
            "Start %s for submission: %s" % (self.action, submission_id))

        # get a submission object (from SubmissionTaskMixin)
        submission_obj = self.get_uid_submission(submission_id)

        # upload data into UID with the proper method (defined in child class)
        status = self.import_data_from_file(submission_obj)

        # if something went wrong, uploaded_cryoweb has token the exception
        # ad update submission.message field
        if status is False:
            message = "Error in %s" % (self.action)
            logger.error(message)

            # this a failure in my import, not the task itself
            return message

        else:
            message = "%s completed for submission: %s" % (
                self.action, submission_id)

            # debug
            logger.info(message)

            # always return something
            return "success"
