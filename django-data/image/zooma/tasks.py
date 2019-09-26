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


class AnnotateTaskMixin():
    name = None
    descripttion = None
    model = None
    annotate_func = None

    def run(self):
        """This function is called when delay is called"""

        logger.debug("Starting %s" % self.name.lower())

        # get all countries without a term
        for term in self.model.objects.filter(term__isnull=True):
            self.annotate_func(term)

        logger.debug("%s completed" % self.name.lower())

        return "success"


class AnnotateCountries(AnnotateTaskMixin, MyTask):
    name = "Annotate Countries"
    description = """Annotate countries with ontologies using Zooma tools"""
    model = DictCountry
    annotate_func = staticmethod(annotate_country)


class AnnotateBreeds(MyTask):
    name = "Annotate Breeds"
    description = """Annotate breeds with ontologies using Zooma tools"""

    def run(self):
        """This function is called when delay is called"""

        logger.debug("Starting %s" % self.name.lower())

        # get all breeds without a term
        for breed in DictBreed.objects.filter(mapped_breed_term__isnull=True):
            annotate_breed(breed)

        logger.debug("%s completed" % self.name.lower())

        return "success"


class AnnotateSpecies(AnnotateTaskMixin, MyTask):
    name = "Annotate Species"
    description = """Annotate species with ontologies using Zooma tools"""
    model = DictSpecie
    annotate_func = staticmethod(annotate_specie)


class AnnotateUberon(AnnotateTaskMixin, MyTask):
    name = "Annotate Uberon"
    description = "Annotate organism parts with ontologies using Zooma tools"
    model = DictUberon
    annotate_func = staticmethod(annotate_uberon)


class AnnotateDictDevelStage(AnnotateTaskMixin, MyTask):
    name = "Annotate DictDevelStage"
    description = (
        "Annotate developmental stages with ontologies using Zooma tools")
    model = DictDevelStage
    annotate_func = staticmethod(annotate_dictdevelstage)


class AnnotateDictPhysioStage(AnnotateTaskMixin, MyTask):
    name = "Annotate DictPhysioStage"
    description = (
        "Annotate physiological stages with ontologies using Zooma tools")
    model = DictPhysioStage
    annotate_func = staticmethod(annotate_dictphysiostage)


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
