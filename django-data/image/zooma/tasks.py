#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 11:27:52 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from celery.utils.log import get_task_logger

# TODO: MyTask need to be moved into common library
from image.celery import app as celery_app, MyTask
from image_app.models import DictCountry, DictBreed, DictSpecie

from .helpers import annotatate_country, annotate_breed, annotate_specie

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
            annotatate_country(country)

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

# --- task registering


# register explicitly task
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(AnnotateCountries)
celery_app.tasks.register(AnnotateBreeds)
celery_app.tasks.register(AnnotateSpecies)
