#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  8 12:34:00 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.core.management.base import BaseCommand
from image_app.models import DictSpecie
from zooma.helpers import useZooma

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Call zooma for species object'

    def handle(self, *args, **options):
        # get all species without a short_term
        for specie in DictSpecie.objects.filter(term__isnull=True):
            logger.debug("Processing %s" % (specie))

            result = useZooma(specie.label, "species")

            # update object (if possible)
            if result:
                url = result['ontologyTerms']
                # https://stackoverflow.com/a/7253830
                term = url.rsplit('/', 1)[-1]

                # check that term have a correct ontology
                # TODO: move this check in useZooma and relate with Ontology
                # table
                if term.split("_")[0] != "NCBITaxon":
                    logger.error(
                        "Got an unexpected term for %s: %s" % (
                            specie, term))

                    # ignore such term
                    continue

                # The ontology seems correct. Annotate!
                logger.info("Updating %s with %s" % (specie, result))
                url = result['ontologyTerms']

                specie.term = term

                # get an int object for such confidence
                confidence = specie.CONFIDENCE.get_value(
                    result["confidence"].lower())

                specie.confidence = confidence
                specie.save()
