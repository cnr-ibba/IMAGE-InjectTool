#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 26 17:21:28 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import logging

from pyUSIrest.usi import Root
from pyUSIrest.exceptions import USIDataError

from django.core.management import BaseCommand

from biosample.helpers import get_manager_auth
from biosample.models import OrphanSubmission
from biosample.tasks.cleanup import get_orphan_samples
from common.constants import SUBMITTED

# Get an instance of a logger
logger = logging.getLogger(__name__)


def create_biosample_submission(root, team):
    logger.debug("Creating a new submission")

    usi_team = root.get_team_by_name(team.name)
    usi_submission = usi_team.create_submission()

    submission = OrphanSubmission(
        usi_submission_name=usi_submission.name)
    submission.save()

    logger.debug("Created submission %s" % submission)
    return usi_submission, submission


def update_submission_status(submission):
    """Set SUBMITTED status to submission"""

    # update submission status
    if submission:
        submission.status = SUBMITTED
        submission.save()


class Command(BaseCommand):
    help = 'Get a JSON for biosample submission'

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Called patch_orphan_samples")

        # get a new auth object
        auth = get_manager_auth()

        # get a new root object
        root = Root(auth)

        # some variables
        count = 1
        old_team = None
        usi_submission = None
        submission = None

        # iterate among orphan sample, create a BioSample submission
        # and then add biosample for patch
        for orphan_sample in get_orphan_samples():
            data, team = orphan_sample['data'], orphan_sample['team']

            if count % 100 == 0 or old_team != team:
                update_submission_status(submission)

                # create a new Biosample submission
                usi_submission, submission = create_biosample_submission(
                    root, team)

                # reset count and old_team
                count = 1
                old_team = team

            # add sample to submission
            try:
                usi_submission.create_sample(data)

            except USIDataError:
                logger.error("Can't remove %s" % data)
                continue

            # update submission count
            submission.samples_count = count
            submission.save()

            # new element
            count += 1

        # update the last submission status
        update_submission_status(submission)

        # end the script
        logger.info("patch_orphan_samples ended")
