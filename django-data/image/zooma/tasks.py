#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 11:27:52 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

from common.tasks import BaseTask
from image.celery import app as celery_app
from image_app.models import DictCountry, DictBreed, DictSpecie, DictUberon

from .helpers import (
    annotate_country, annotate_breed, annotate_specie, annotate_uberon)

# Get an instance of a logger
logger = get_task_logger(__name__)


class AnnotateCountries(BaseTask):
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


class AnnotateBreeds(BaseTask):
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


class AnnotateSpecies(BaseTask):
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


class AnnotateUberon(BaseTask):
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

# --- task registering


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(AnnotateCountries)
celery_app.tasks.register(AnnotateBreeds)
celery_app.tasks.register(AnnotateSpecies)
celery_app.tasks.register(AnnotateUberon)
