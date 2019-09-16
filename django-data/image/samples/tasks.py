#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:37 2019
@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from django.db import transaction

from common.constants import ERROR, NEED_REVISION
from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Sample, Name
from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from validation.models import ValidationSummary

# Get an instance of a logger
logger = get_task_logger(__name__)


class BatchDeleteSamples(MyTask):
    name = "Batch delete samples"
    description = """Batch remove samples"""

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # get submission object
        submission_obj = Submission.objects.get(pk=kwargs['submission_id'])

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = (
            "Error in sample batch delete: %s" % (str(exc)))
        submission_obj.save()

        send_message(submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in sample batch delete for submission: %s" % (
                submission_obj.id),
            ("Something goes wrong in batch delete for samples. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin

    def run(self, submission_id, sample_ids):
        """Function for batch update attribute in animals
        Args:
            submission_id (int): id of submission
            sample_ids (list): set with ids to delete
        """

        # get a submisision object
        submission_obj = Submission.objects.get(pk=submission_id)

        logger.info("Start batch delete for samples")
        success_ids = list()
        failed_ids = list()

        for sample_id in sample_ids:
            try:
                name = Name.objects.get(
                    name=sample_id, submission=submission_obj)

                sample_obj = Sample.objects.get(name=name)

                with transaction.atomic():
                    sample_obj.delete()
                    name.delete()
                success_ids.append(sample_id)

            except Name.DoesNotExist:
                failed_ids.append(sample_id)

            except Sample.DoesNotExist:
                failed_ids.append(sample_id)

        # Update submission
        submission_obj.refresh_from_db()
        submission_obj.status = NEED_REVISION

        if len(failed_ids) != 0:
            submission_obj.message = f"You've removed {len(success_ids)} " \
                f"samples. It wasn't possible to find records with these " \
                f"ids: {', '.join(failed_ids)}. Rerun validation please!"
        else:
            submission_obj.message = f"You've removed {len(success_ids)} " \
                f"samples. Rerun validation please!"

        submission_obj.save()

        summary_obj, created = ValidationSummary.objects.get_or_create(
            submission=submission_obj, type='sample')
        summary_obj.reset_all_count()

        send_message(
            submission_obj, construct_validation_message(submission_obj)
        )

        logger.info("batch delete for samples completed")

        return 'success'


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(BatchDeleteSamples)
