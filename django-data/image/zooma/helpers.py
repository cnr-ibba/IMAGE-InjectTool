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


def annotate_generic(model, zooma_type):
    """Annotate a generic DictTable

    Args:
        model (:py:class:`image_app.models.DictBase`): A DictBase istance
        zooma_type (str): the type of zooma annotation (country, species, ...)
    """

    logger.debug("Processing %s" % (model))

    result = use_zooma(model.label, zooma_type)

    # update object (if possible)
    if result:
        url = result['ontologyTerms']
        # https://stackoverflow.com/a/7253830
        term = url.rsplit('/', 1)[-1]

        # The ontology seems correct. Annotate!
        logger.info("Updating %s with %s" % (model, result))
        url = result['ontologyTerms']

        model.term = term

        # get an int object for such confidence
        confidence = CONFIDENCES.get_value(
            result["confidence"].lower())

        model.confidence = confidence
        model.save()


def annotate_country(country_obj):
    """Annotate a country object using Zooma"""

    annotate_generic(country_obj, "country")


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

        # The ontology seems correct. Annotate!
        logger.info("Updating %s with %s" % (breed_obj, result))
        url = result['ontologyTerms']

        # this is slight different from annotate_generic
        breed_obj.mapped_breed_term = term
        breed_obj.mapped_breed = result['text']

        # get an int object for such confidence
        confidence = CONFIDENCES.get_value(
            result["confidence"].lower())

        breed_obj.confidence = confidence
        breed_obj.save()


def annotate_specie(specie_obj):
    """Annotate a specie object using Zooma"""

    annotate_generic(specie_obj, "species")


def annotate_uberon(uberon_obj):
    """Annotate an organism part object using Zooma"""

    annotate_generic(uberon_obj, "organism part")


def annotate_dictdevelstage(dictdevelstage_obj):
    """Annotate an developmental stage part object using Zooma"""

    annotate_generic(dictdevelstage_obj, "developmental stage")


def annotate_dictphysiostage(dictphysiostage_obj):
    """Annotate an physiological stage object using Zooma"""

    annotate_generic(dictphysiostage_obj, "physiological stage")
