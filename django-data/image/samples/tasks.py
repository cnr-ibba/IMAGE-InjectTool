#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:37 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from django.db import transaction

from common.constants import NEED_REVISION
from common.tasks import BaseTask, NotifyAdminTaskMixin
from image.celery import app as celery_app
from image_app.models import Sample, Name
from submissions.tasks import BatchUpdateMixin, SubmissionTaskMixin
from validation.models import ValidationSummary

# Get an instance of a logger
logger = get_task_logger(__name__)


class BatchDeleteSamples(SubmissionTaskMixin, NotifyAdminTaskMixin, BaseTask):
    name = "Batch delete samples"
    description = """Batch remove samples"""
    action = "batch delete samples"

    def run(self, submission_id, sample_ids):
        """Function for batch update attribute in animals
        Args:
            submission_id (int): id of submission
            sample_ids (list): set with ids to delete
        """

        # get a submission object (from SubmissionTaskMixin)
        submission_obj = self.get_uid_submission(submission_id)

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

        if len(failed_ids) != 0:
            message = f"You've removed {len(success_ids)} " \
                f"samples. It wasn't possible to find records with these " \
                f"ids: {', '.join(failed_ids)}. Rerun validation please!"
        else:
            message = f"You've removed {len(success_ids)} " \
                f"samples. Rerun validation please!"

        summary_obj, created = ValidationSummary.objects.get_or_create(
            submission=submission_obj, type='sample')
        summary_obj.reset_all_count()

        # mark submission with NEED_REVISION and send message
        self.update_submission_status(
            submission_obj,
            NEED_REVISION,
            message,
            construct_message=True
        )

        logger.info("batch delete for samples completed")

        return 'success'


class BatchUpdateSamples(BatchUpdateMixin, NotifyAdminTaskMixin, BaseTask):
    name = "Batch update samples"
    description = """Batch update of field in samples"""
    action = "batch update samples"

    # defined in common.tasks.BatchUpdateMixin
    item_cls = Sample

    def run(self, submission_id, sample_ids, attribute):
        """Function for batch update attribute in samples
        Args:
            submission_id (int): id of submission
            sample_ids (dict): dict with id and values to update
            attribute (str): attribute to update
        """

        logger.info("Start batch update for samples")
        self.batch_update(submission_id, sample_ids, attribute)

        return 'success'


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(BatchDeleteSamples)
celery_app.tasks.register(BatchUpdateSamples)
