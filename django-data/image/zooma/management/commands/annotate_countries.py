#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  9 11:21:45 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.core.management.base import BaseCommand
from image_app.models import DictCountry
from zooma.helpers import useZooma

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Call zooma for species object'

    def handle(self, *args, **options):
        # get all countries without a term
        for country in DictCountry.objects.filter(term__isnull=True):
            logger.debug("Processing %s" % (country))

            result = useZooma(country.label, "country")

            # update object (if possible)
            if result:
                url = result['ontologyTerms']
                # https://stackoverflow.com/a/7253830
                term = url.rsplit('/', 1)[-1]

                # check that term have a correct ontology
                # TODO: move this check in useZooma and relate with Ontology
                # table
                if term.split("_")[0] != "GAZ":
                    logger.error(
                        "Got an unexpected term for %s: %s" % (
                            country, term))

                    # ignore such term
                    continue

                # The ontology seems correct. Annotate!
                logger.info("Updating %s with %s" % (country, result))
                url = result['ontologyTerms']

                country.term = term

                # get an int object for such confidence
                confidence = country.CONFIDENCE.get_value(
                    result["confidence"].lower())

                country.confidence = confidence
                country.save()
