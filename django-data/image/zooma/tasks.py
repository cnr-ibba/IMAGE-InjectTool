#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 11:27:52 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import time

from celery import group
from celery.utils.log import get_task_logger

from common.tasks import redis_lock
from image.celery import app as celery_app, MyTask
from image_app.models import (
    DictCountry, DictBreed, DictSpecie, DictUberon, DictDevelStage,
    DictPhysioStage)

from .helpers import (
    annotate_country, annotate_breed, annotate_specie, annotate_uberon,
    annotate_dictdevelstage, annotate_dictphysiostage)

# Get an instance of a logger
logger = get_task_logger(__name__)


class AnnotateCountries(MyTask):
    name = "Annotate Countries"
    description = """Annotate countries with ontologies using Zooma tools"""

    def run(self):
        """This function is called when delay is called"""

        logger.debug("Starting annotate countries")

        # get all countries without a term
        for country in DictCountry.objects.filter(term__isnull=True):
            annotate_country(country)

        logger.debug("Annotate countries completed")

        return "success"


class AnnotateBreeds(MyTask):
    name = "Annotate Breeds"
    description = """Annotate breeds with ontologies using Zooma tools"""

    def run(self):
        """This function is called when delay is called"""

        logger.debug("Starting annotate breeds")

        # get all breeds without a term
        for breed in DictBreed.objects.filter(mapped_breed_term__isnull=True):
            annotate_breed(breed)

        logger.debug("Annotate breeds completed")

        return "success"


class AnnotateSpecies(MyTask):
    name = "Annotate Species"
    description = """Annotate species with ontologies using Zooma tools"""

    def run(self):
        """This function is called when delay is called"""

        logger.debug("Starting annotate species")

        # get all breeds without a term
        for specie in DictSpecie.objects.filter(term__isnull=True):
            annotate_specie(specie)

        logger.debug("Annotate species completed")

        return "success"


class AnnotateUberon(MyTask):
    name = "Annotate Uberon"
    description = "Annotate organism parts with ontologies using Zooma tools"

    def run(self):
        """This function is called when delay is called"""

        logger.debug("Starting annotate uberon")

        # get all breeds without a term
        for part in DictUberon.objects.filter(term__isnull=True):
            annotate_uberon(part)

        logger.debug("Annotate uberon completed")

        return "success"


class AnnotateDictDevelStage(MyTask):
    name = "Annotate DictDevelStage"
    description = (
        "Annotate developmental stages with ontologies using Zooma tools")

    def run(self):
        """This function is called when delay is called"""

        logger.debug("Starting annotate developmental stages")

        # get all breeds without a term
        for stage in DictDevelStage.objects.filter(term__isnull=True):
            annotate_dictdevelstage(stage)

        logger.debug("Annotate developmental stages completed")

        return "success"


class AnnotateDictPhysioStage(MyTask):
    name = "Annotate DictPhysioStage"
    description = (
        "Annotate physiological stages with ontologies using Zooma tools")

    def run(self):
        """This function is called when delay is called"""

        logger.debug("Starting annotate physiological stages")

        # get all breeds without a term
        for stage in DictPhysioStage.objects.filter(term__isnull=True):
            annotate_dictphysiostage(stage)

        logger.debug("Annotate physiological stages completed")

        return "success"


class AnnotateAll(MyTask):
    name = "Annotate All"
    description = """Annotate all dict tables using Zooma"""
    lock_id = "AnnotateAll"

    def run(self):
        """
        This function is called when delay is called. It will acquire a lock
        in redis, so those tasks are mutually exclusive

        Returns:
            str: success if everything is ok. Different messages if task is
            already running or exception is caught"""

        # debugging instance
        self.debug_task()

        # blocking condition: get a lock or exit with statement
        with redis_lock(
                self.lock_id, blocking=False, expire=False) as acquired:
            if acquired:
                # do stuff and return something
                return self.call_zooma()

        message = "%s already running!" % (self.name)

        logger.warning(message)

        return message

    def call_zooma(self):
        """Start all task in a group and wait for a reply"""

        tasks = [
            AnnotateCountries(), AnnotateBreeds(), AnnotateSpecies(),
            AnnotateUberon(), AnnotateDictDevelStage(),
            AnnotateDictPhysioStage()
        ]

        # instantiate the group
        annotate_task = group([task.s() for task in tasks])

        logger.debug("Starting task %s" % (annotate_task))

        # start the group task - shortcut for apply_asyinc
        result = annotate_task.delay()

        logger.debug(result)

        while result.waiting() is True:
            logger.debug("Waiting for zooma tasks to complete")
            time.sleep(10)

        # get results
        results = result.join()

        for i, task in enumerate(tasks):
            logger.debug("%s returned %s" % (task.name, results[i]))

        return "success"


# --- task registering


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(AnnotateCountries)
celery_app.tasks.register(AnnotateBreeds)
celery_app.tasks.register(AnnotateSpecies)
celery_app.tasks.register(AnnotateUberon)
celery_app.tasks.register(AnnotateDictDevelStage)
celery_app.tasks.register(AnnotateDictPhysioStage)
celery_app.tasks.register(AnnotateAll)
