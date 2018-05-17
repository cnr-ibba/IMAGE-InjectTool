#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  9 11:25:09 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.core.management.base import BaseCommand
from image_app.models import DictBreed
from zooma.helpers import useZooma

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Call zooma for dictbreed object. Fill table if possible'

    def handle(self, *args, **options):
        # get all species without a term
        for breed in DictBreed.objects.filter(mapped_breed_term__isnull=True):
            logger.debug("Processing %s" % (breed))

            result = useZooma(
                breed.supplied_breed, "breed")

            # update object (if possible)
            if result:
                url = result['ontologyTerms']
                # https://stackoverflow.com/a/7253830
                term = url.rsplit('/', 1)[-1]

                # check that term have a correct ontology
                # TODO: move this check in useZooma and relate with Ontology
                # table
                if term.split("_")[0] != "LBO":
                    logger.error(
                        "Got an unexpected term for %s: %s" % (
                            breed, term))

                    # ignore such term
                    continue

                # The ontology seems correct. Annotate!
                logger.info("Updating %s with %s" % (breed, result))
                url = result['ontologyTerms']

                breed.mapped_breed_term = term
                breed.mapped_breed = result['text']

                # get an int object for such confidence
                confidence = breed.CONFIDENCE.get_value(
                    result["confidence"].lower())

                breed.confidence = confidence
                breed.save()
