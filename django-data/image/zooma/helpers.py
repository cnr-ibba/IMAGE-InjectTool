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


def call_zooma(label, zooma_type):
    """
    Wrapper around use_zooma: call zooma or catch exception

    Parameters
    ----------
    label : str
        Zooma query temr.
    zooma_type : str
        Zooma query type (species, breed, ...).

    Returns
    -------
    result : dict
        The results of use_zooma or None

    """

    result = None

    try:
        result = use_zooma(label, zooma_type)

    except Exception as exc:
        logger.error("Error in calling zooma: %s" % str(exc))

    return result


def annotate_generic(model, zooma_type):
    """Annotate missing terms from a generic DictTable

    Args:
        model (:py:class:`uid.models.DictBase`): A DictBase istance
        zooma_type (str): the type of zooma annotation (country, species, ...)
    """

    logger.debug("Processing %s" % (model))

    result = call_zooma(model.label, zooma_type)

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
    """Annotate country objects using Zooma"""

    annotate_generic(country_obj, "country")


def annotate_breed(breed_obj):
    """Annotate breed objects using Zooma"""

    logger.debug("Processing %s" % (breed_obj))

    result = call_zooma(breed_obj.supplied_breed, "breed")

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
    """Annotate specie objects using Zooma"""

    annotate_generic(specie_obj, "species")


def annotate_organismpart(uberon_obj):
    """Annotate organism part objects using Zooma"""

    annotate_generic(uberon_obj, "organism part")


def annotate_develstage(dictdevelstage_obj):
    """Annotate developmental stage objects using Zooma"""

    annotate_generic(dictdevelstage_obj, "developmental stage")


def annotate_physiostage(dictphysiostage_obj):
    """Annotate physiological stage objects using Zooma"""

    annotate_generic(dictphysiostage_obj, "physiological stage")
