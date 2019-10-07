#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:37 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from django.db import transaction

from common.constants import NEED_REVISION
from common.tasks import BatchUpdateMixin, BatchFailurelMixin, BaseTask
from image.celery import app as celery_app
from image_app.models import Submission, Sample, Name
from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from validation.models import ValidationSummary

# Get an instance of a logger
logger = get_task_logger(__name__)


class BatchDeleteSamples(BatchFailurelMixin, BaseTask):
    name = "Batch delete samples"
    description = """Batch remove samples"""
    batch_type = "delete"
    model_type = "sample"
    submission_cls = Submission

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


class BatchUpdateSamples(BatchFailurelMixin, BatchUpdateMixin, BaseTask):
    name = "Batch update samples"
    description = """Batch update of field in samples"""
    batch_type = "update"
    model_type = "sample"

    item_cls = Sample
    submission_cls = Submission

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
