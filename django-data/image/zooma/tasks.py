#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 11:27:52 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery import group
from celery.utils.log import get_task_logger

from common.tasks import ExclusiveTask, NotifyAdminTaskMixin
from image.celery import app as celery_app
from image_app.models import (
    DictCountry, DictBreed, DictSpecie, DictUberon, DictDevelStage,
    DictPhysioStage)

from .helpers import (
    annotate_country, annotate_breed, annotate_specie, annotate_uberon,
    annotate_dictdevelstage, annotate_dictphysiostage)

# Get an instance of a logger
logger = get_task_logger(__name__)


class AnnotateTaskMixin(NotifyAdminTaskMixin):
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


class AnnotateCountries(AnnotateTaskMixin, ExclusiveTask):
    name = "Annotate Countries"
    description = """Annotate countries with ontologies using Zooma tools"""
    model = DictCountry
    annotate_func = staticmethod(annotate_country)


class AnnotateBreeds(AnnotateTaskMixin, ExclusiveTask):
    name = "Annotate Breeds"
    description = """Annotate breeds with ontologies using Zooma tools"""
    model = DictBreed
    annotate_func = staticmethod(annotate_breed)


class AnnotateSpecies(AnnotateTaskMixin, ExclusiveTask):
    name = "Annotate Species"
    description = """Annotate species with ontologies using Zooma tools"""
    model = DictSpecie
    annotate_func = staticmethod(annotate_specie)


class AnnotateUberon(AnnotateTaskMixin, ExclusiveTask):
    name = "Annotate Uberon"
    description = "Annotate organism parts with ontologies using Zooma tools"
    model = DictUberon
    annotate_func = staticmethod(annotate_uberon)


class AnnotateDictDevelStage(AnnotateTaskMixin, ExclusiveTask):
    name = "Annotate DictDevelStage"
    description = (
        "Annotate developmental stages with ontologies using Zooma tools")
    model = DictDevelStage
    annotate_func = staticmethod(annotate_dictdevelstage)


class AnnotateDictPhysioStage(AnnotateTaskMixin, ExclusiveTask):
    name = "Annotate DictPhysioStage"
    description = (
        "Annotate physiological stages with ontologies using Zooma tools")
    model = DictPhysioStage
    annotate_func = staticmethod(annotate_dictphysiostage)


class AnnotateAll(ExclusiveTask):
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

        # forget about called tasks and exit

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
