#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 15:49:04 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Functions adapted from Jun Fan misc.py and use_zooma.py python scripts
"""

import logging

from image_validation.use_ontology import use_zooma

from common.constants import CONFIDENCES


# Get an instance of a logger
logger = logging.getLogger(__name__)


def annotate_country(country_obj):
    """Annotate a country object using Zooma"""

    logger.debug("Processing %s" % (country_obj))

    result = use_zooma(country_obj.label, "country")

    # update object (if possible)
    if result:
        url = result['ontologyTerms']
        # https://stackoverflow.com/a/7253830
        term = url.rsplit('/', 1)[-1]

        # check that term have a correct ontology
        # TODO: move this check in use_zooma and relate with Ontology
        # table
        if term.split("_")[0] != "NCIT":
            logger.error(
                "Got an unexpected term for %s: %s" % (
                    country_obj, term))

            # ignore such term
            return

        # The ontology seems correct. Annotate!
        logger.info("Updating %s with %s" % (country_obj, result))
        url = result['ontologyTerms']

        country_obj.term = term

        # get an int object for such confidence
        confidence = CONFIDENCES.get_value(
            result["confidence"].lower())

        country_obj.confidence = confidence
        country_obj.save()


def annotate_breed(breed_obj):
    """Annotate a breed object using Zooma"""

    logger.debug("Processing %s" % (breed_obj))

    result = use_zooma(
        breed_obj.supplied_breed, "breed")

    # update object (if possible)
    if result:
        url = result['ontologyTerms']
        # https://stackoverflow.com/a/7253830
        term = url.rsplit('/', 1)[-1]

        # check that term have a correct ontology
        # TODO: move this check in use_zooma and relate with Ontology
        # table
        if term.split("_")[0] != "LBO":
            logger.error(
                "Got an unexpected term for %s: %s" % (
                    breed_obj, term))

            # ignore such term
            return

        # The ontology seems correct. Annotate!
        logger.info("Updating %s with %s" % (breed_obj, result))
        url = result['ontologyTerms']

        breed_obj.mapped_breed_term = term
        breed_obj.mapped_breed = result['text']

        # get an int object for such confidence
        confidence = CONFIDENCES.get_value(
            result["confidence"].lower())

        breed_obj.confidence = confidence
        breed_obj.save()


def annotate_specie(specie_obj):
    """Annotate a specie object using Zooma"""

    logger.debug("getting ontology term for %s" % (specie_obj))

    result = use_zooma(specie_obj.label, "species")

    # update object (if possible)
    if result:
        url = result['ontologyTerms']
        # https://stackoverflow.com/a/7253830
        term = url.rsplit('/', 1)[-1]

        # check that term have a correct ontology
        # TODO: move this check in use_zooma and relate with Ontology
        # table
        if term.split("_")[0] != "NCBITaxon":
            logger.error(
                "Got an unexpected term for %s: %s" % (
                    specie_obj, term))

            # ignore such term
            return

        # The ontology seems correct. Annotate!
        logger.info("Updating %s with %s" % (specie_obj, result))
        url = result['ontologyTerms']

        specie_obj.term = term

        # get an int object for such confidence
        confidence = CONFIDENCES.get_value(
            result["confidence"].lower())

        specie_obj.confidence = confidence
        specie_obj.save()


def annotate_uberon(uberon_obj):
    """Annotate an organism part object using Zooma"""

    logger.debug("getting ontology term for %s" % (uberon_obj))

    result = use_zooma(uberon_obj.label, "organism part")

    # update object (if possible)
    if result:
        url = result['ontologyTerms']
        # https://stackoverflow.com/a/7253830
        term = url.rsplit('/', 1)[-1]

        # check that term have a correct ontology
        # TODO: move this check in use_zooma and relate with Ontology
        # table
        if term.split("_")[0] != "UBERON":
            logger.error(
                "Got an unexpected term for %s: %s" % (
                    uberon_obj, term))

            # ignore such term
            return

        # The ontology seems correct. Annotate!
        logger.info("Updating %s with %s" % (uberon_obj, result))
        url = result['ontologyTerms']

        uberon_obj.term = term

        # get an int object for such confidence
        confidence = CONFIDENCES.get_value(
            result["confidence"].lower())

        uberon_obj.confidence = confidence
        uberon_obj.save()
