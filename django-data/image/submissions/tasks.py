#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 16:10:06 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from common.constants import ERROR

from .helpers import send_message

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ImportGenericTaskMixin():
    name = None
    description = None
    submission_model = None
    datasource_type = None

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # get submission object
        submission_obj = self.submission_model.objects.get(pk=args[0])

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = (
            "Error in %s loading: %s" % (self.datasource_type, str(exc)))
        submission_obj.save()

        # send async message
        send_message(submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in %s loading: %s" % (
                self.datasource_type, args[0]),
            ("Something goes wrong with %s loading. Please report "
             "this to InjectTool team\n\n %s" % (
                self.datasource_type,
                str(einfo))),
        )

        # TODO: submit mail to admin

    def run(self, submission_id):
        """a function to upload data into UID"""

        logger.info(
            "Start import from %s for submission: %s" % (
                self.datasource_type, submission_id))

        # get a submission object
        submission = self.submission_model.objects.get(pk=submission_id)

        # upload data into UID with the proper method (defined in child class)
        status = self.import_data_from_file(submission)

        # if something went wrong, uploaded_cryoweb has token the exception
        # ad update submission.message field
        if status is False:
            message = "Error in uploading %s data" % (self.datasource_type)
            logger.error(message)

            # this a failure in my import, not the task itself
            return message

        else:
            message = "%s import completed for submission: %s" % (
                self.datasource_type, submission_id)

            # debug
            logger.info(message)

            # always return something
            return "success"
