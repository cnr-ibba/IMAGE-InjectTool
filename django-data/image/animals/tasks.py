#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:37 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from django.db import transaction

from common.constants import ERROR, NEED_REVISION
from common.tasks import BatchUpdateMixin
from image.celery import app as celery_app, MyTask
from image_app.models import Submission, Animal, Name
from submissions.helpers import send_message
from validation.helpers import construct_validation_message
from validation.models import ValidationSummary

# Get an instance of a logger
logger = get_task_logger(__name__)


class BatchDeleteAnimals(MyTask):
    name = "Batch delete animals"
    description = """Batch remove animals and associated samples"""

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        submission_id, animal_ids = args[0], args[1]

        logger.error(
            ("BatchDeleteAnimals called with submission_id: %s and "
             "animal_ids: %s" % (submission_id, animal_ids))
        )

        # get submission object
        submission_obj = Submission.objects.get(pk=submission_id)

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = (
            "Error in animal batch delete: %s" % (str(exc)))
        submission_obj.save()

        send_message(submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in animal batch delete for submission: %s" % (
                submission_obj.id),
            ("Something goes wrong in batch delete for animals. Please report "
             "this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin

    def run(self, submission_id, animal_ids):
        """Function for batch update attribute in animals
        Args:
            submission_id (int): id of submission
            animal_ids (list): set with ids to delete
        """

        # get a submisision object
        submission_obj = Submission.objects.get(pk=submission_id)

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

        # Update submission
        submission_obj.refresh_from_db()
        submission_obj.status = NEED_REVISION

        if len(failed_ids) != 0:
            submission_obj.message = f"You've removed {len(success_ids)} " \
                f"animals. It wasn't possible to find records with these " \
                f"ids: {', '.join(failed_ids)}. Rerun validation please!"
        else:
            submission_obj.message = f"You've removed {len(success_ids)} " \
                f"animals. Rerun validation please!"

        submission_obj.save()

        summary_obj, created = ValidationSummary.objects.get_or_create(
            submission=submission_obj, type='animal')
        summary_obj.reset()

        # after removing animal associated samples, we need to update also
        # sample all count
        summary_obj, created = ValidationSummary.objects.get_or_create(
            submission=submission_obj, type='sample')
        summary_obj.reset()

        # TODO: validation summary could be updated relying database, instead
        # doing validation. Define a method in validation.helpers to update
        # summary relying only on database

        send_message(
            submission_obj, construct_validation_message(submission_obj)
        )

        logger.info("batch delete for animals completed")

        return 'success'


class BatchUpdateAnimals(MyTask, BatchUpdateMixin):
    name = "Batch update animals"
    description = """Batch update of field in animals"""

    item_cls = Animal
    submission_cls = Submission

    # Ovverride default on failure method
    # This is not a failed validation for a wrong value, this is an
    # error in task that mean an error in coding
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))

        # get submission object
        submission_obj = Submission.objects.get(pk=args[0])

        # mark submission with ERROR
        submission_obj.status = ERROR
        submission_obj.message = ("Error in batch update for animals: %s"
                                  % (str(exc)))
        submission_obj.save()

        send_message(submission_obj)

        # send a mail to the user with the stacktrace (einfo)
        submission_obj.owner.email_user(
            "Error in batch update for animals: %s" % (args[0]),
            ("Something goes wrong  in batch update for animals. Please "
             "report this to InjectTool team\n\n %s" % str(einfo)),
        )

        # TODO: submit mail to admin

    def run(self, submission_id, animal_ids, attribute):
        """Function for batch update attribute in animals
        Args:
            submission_id (int): id of submission
            animal_ids (dict): dict with id and values to update
            attribute (str): attribute to update
        """

        logger.info("Start batch update for animals")
        super(BatchUpdateAnimals, self).batch_update(submission_id, animal_ids,
                                                     attribute)
        return 'success'


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(BatchDeleteAnimals)
celery_app.tasks.register(BatchUpdateAnimals)
