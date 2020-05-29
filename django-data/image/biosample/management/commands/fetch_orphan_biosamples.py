#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 28 16:06:56 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>

Fetch the Orphan submissions and track BioSamples removal

"""

import json
import logging

import pyUSIrest.usi

from django.core.management import BaseCommand

from biosample.helpers import get_manager_auth
from biosample.models import OrphanSubmission
from biosample.tasks.retrieval import FetchStatusHelper
from common.constants import SUBMITTED, NEED_REVISION


# Get an instance of a logger
logger = logging.getLogger(__name__)


class SubmissionHelper(FetchStatusHelper):
    def __init__(self, root, usi_submission, can_finalize=False):
        self.root = root
        self.usi_submission = usi_submission
        self.can_finalize = can_finalize
        self.submission_name = usi_submission.usi_submission_name

        logger.info(
            "Getting info for usi submission '%s'" % (self.submission_name))

        self.submission = root.get_submission_by_name(
            submission_name=self.submission_name)

    # override finalize method
    def finalize(self):
        """Finalize a submission by closing document and send it to
        biosample"""

        if not self.can_finalize:
            # skip finalizing a submission
            logger.warning(
                "Ignoring finalization: please call with '--finalize'"
                " argument")
            return

        logger.info("Finalizing submission '%s'" % (
            self.submission_name))

        # get errors for a submission
        errors = self.submission.has_errors()

        # collect all error messages in a list
        messages = []

        if True in errors:
            # get sample with errors then update database
            samples = self.submission.get_samples(has_errors=True)

            for sample in samples:
                if sample.has_errors():
                    logger.error("%s has errors!!!" % sample)

                    # mark this sample since has problems
                    errorMessages = self.sample_has_errors(sample)

                    # append this into error messages list
                    messages.append(errorMessages)

                # if a sample has no errors, status will be the same

            logger.error(
                "Errors for submission: '%s'" % (self.submission_name))
            logger.error("Fix them, then finalize")

            # report error
            message = json.dumps(messages, indent=2)

            # Update status for biosample.models.Submission
            self.usi_submission.status = NEED_REVISION
            self.usi_submission.message = message
            self.usi_submission.save()

        else:
            # TODO: model and test exception in finalization
            self.submission.finalize()

    # override complete method
    def complete(self):
        """Complete a submission and fetch biosample names"""

        logger.info("SubmissionHelper.complete() called")

    # custom implementation: here I don't have a record in UID and I
    # can't use the base method of this class
    def sample_has_errors(self, sample):
        """
        Get USI error for sample

        Args:
            sample (pyUSIrest.usi.sample): a USI sample object
        """

        # track status in db like FetchStatusHelper
        orphan_sample = self.usi_submission.submission_data.get(
            biosample_id=sample.accession)
        orphan_sample.status = NEED_REVISION
        orphan_sample.save()

        # get a USI validation result
        validation_result = sample.get_validation_result()

        # track errors  in validation tables
        errorMessages = validation_result.errorMessages

        # return an error for each object
        return {str(sample): errorMessages}


class Command(BaseCommand):
    help = 'Fetch the Orphan submissions and track BioSamples removal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--finalize',
            default=False,
            action='store_true',
        )

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Called fetch_orphan_biosamples")

        # Ok get all Orphaned BioSample submission in SUBMITTED status
        qs = OrphanSubmission.objects.filter(status=SUBMITTED)

        if qs.count() > 0:
            # ok do stuff
            auth = get_manager_auth()
            root = pyUSIrest.usi.Root(auth)

            for orphan_submission in qs:
                submission_helper = SubmissionHelper(
                    root,
                    orphan_submission,
                    options['finalize'])
                submission_helper.check_submission_status()

        # call commands and fill tables.
        logger.info("fetch_orphan_biosamples finished")
