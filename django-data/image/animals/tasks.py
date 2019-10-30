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
from uid.models import Animal, Name
from submissions.tasks import BatchUpdateMixin, SubmissionTaskMixin
from validation.models import ValidationSummary

# Get an instance of a logger
logger = get_task_logger(__name__)


class BatchDeleteAnimals(SubmissionTaskMixin, NotifyAdminTaskMixin, BaseTask):
    name = "Batch delete animals"
    description = """Batch remove animals and associated samples"""
    action = "batch delete animals"

    def run(self, submission_id, animal_ids):
        """Function for batch update attribute in animals
        Args:
            submission_id (int): id of submission
            animal_ids (list): set with ids to delete
        """

        # get a submission object (from SubmissionTaskMixin)
        submission_obj = self.get_uid_submission(submission_id)

        logger.info("Start batch delete for animals")
        success_ids = list()
        failed_ids = list()

        for animal_id in animal_ids:
            try:
                name = Name.objects.get(
                    name=animal_id, submission=submission_obj)

                animal_object = Animal.objects.get(name=name)
                samples = animal_object.sample_set.all()

                with transaction.atomic():
                    for sample in samples:
                        sample_name = sample.name
                        sample.delete()
                        sample_name.delete()

                    logger.debug("Clearing all childs from this animal")
                    name.mother_of.clear()
                    name.father_of.clear()

                    # delete this animal object
                    logger.debug(
                        "Deleting animal:%s and name:%s" % (
                            animal_object, name))
                    animal_object.delete()
                    name.delete()

                success_ids.append(animal_id)

            except Name.DoesNotExist:
                failed_ids.append(animal_id)

            except Animal.DoesNotExist:
                failed_ids.append(animal_id)

        if len(failed_ids) != 0:
            message = f"You've removed {len(success_ids)} " \
                f"animals. It wasn't possible to find records with these " \
                f"ids: {', '.join(failed_ids)}. Rerun validation please!"
        else:
            message = f"You've removed {len(success_ids)} " \
                f"animals. Rerun validation please!"

        summary_obj, created = ValidationSummary.objects.get_or_create(
            submission=submission_obj, type='animal')
        summary_obj.reset()

        # after removing animal associated samples, we need to update also
        # sample all count
        summary_obj, created = ValidationSummary.objects.get_or_create(
            submission=submission_obj, type='sample')
        summary_obj.reset()

        # mark submission with NEED_REVISION and send message
        self.update_submission_status(
            submission_obj,
            NEED_REVISION,
            message,
            construct_message=True
        )

        # TODO: validation summary could be updated relying database, instead
        # doing validation. Define a method in validation.helpers to update
        # summary relying only on database

        logger.info("batch delete for animals completed")

        return 'success'


class BatchUpdateAnimals(BatchUpdateMixin, NotifyAdminTaskMixin, BaseTask):
    name = "Batch update animals"
    description = """Batch update of field in animals"""
    action = "batch update animals"

    # defined in common.tasks.BatchUpdateMixin
    item_cls = Animal

    def run(self, submission_id, animal_ids, attribute):
        """Function for batch update attribute in animals
        Args:
            submission_id (int): id of submission
            animal_ids (dict): dict with id and values to update
            attribute (str): attribute to update
        """

        logger.info("Start batch update for animals")
        self.batch_update(submission_id, animal_ids, attribute)
        return 'success'


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(BatchDeleteAnimals)
celery_app.tasks.register(BatchUpdateAnimals)
