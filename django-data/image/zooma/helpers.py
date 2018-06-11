#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 15:49:04 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Functions adapted from Jun Fan misc.py and use_zooma.py python scripts
"""

import re
import logging
import urllib

import requests

from .constants import ZOOMA_URL, ONTOLOGIES, TAXONOMY_URL


# Get an instance of a logger
logger = logging.getLogger(__name__)


def to_camel_case(input_str):
    """
    Convert a string using CamelCase convention
    """

    input_str = input_str.replace("_", " ")
    components = input_str.split(' ')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0].lower() + ''.join(x.title() for x in components[1:])


def from_camel_case(lower_camel):
    """
    Split a lower camel case string in words
    https://stackoverflow.com/a/1176023
    """

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', lower_camel)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).lower()


def useZooma(term, category):
    # replacing spaces with +
    newTerm = term.replace(" ", "+")

    # defining params with default filters
    params = {
        'propertyValue': newTerm,
        'filter': "required:[ena],ontologies:[%s]" % (",".join(ONTOLOGIES))
    }

    category = from_camel_case(category)

    if (category == "species"):  # necessary if
        # renaming species categories
        category = "organism"

        # species, only search NCBI taxonomy ontology
        params["filter"] = "required:[ena],ontologies:[NCBITaxon]"

    elif (category == "breed"):
        # breed, only search Livestock Breed Ontology
        params["filter"] = "required:[ena],ontologies:[lbo]"

    elif (category == "country"):
        # country, only search GAZ Ontology
        params["filter"] = "required:[ena],ontologies:[gaz]"
    else:
        # according to IMAGE ruleset, only these ontology libraries are
        # allowed in the ruleset, so not search others, gaz is for countries
        params["filter"] = "required:[ena],ontologies:[efo,uberon,obi,pato]"

    highResult = {}
    goodResult = {}
    result = {}

    # debug
    logger.debug("Calling zooma with %s" % (params))

    request = requests.get(ZOOMA_URL, params=params)

    # print (json.dumps(request.json(), indent=4, sort_keys=True))
    logger.debug(request)

    # read results
    results = request.json()

    # a warn
    if len(results) > 1:
        logger.warn("Got %s results for %s" % (len(results), params))

        for elem in results:
            logger.warn(elem['annotatedProperty'])

    for elem in results:
        detectedType = elem['annotatedProperty']['propertyType']

        # the type must match the given one or be null
        if (detectedType is None or detectedType == category):
            confidence = elem['confidence'].lower()
            propertyValue = elem['annotatedProperty']['propertyValue']
            semanticTag = elem['_links']['olslinks'][0]['semanticTag']

            # potential useful data: ['_links']['olslinks'][0]['href']:
            # https://www.ebi.ac.uk/ols/api/terms?iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FUBERON_0002106
            if (confidence == "high"):
                highResult[propertyValue] = semanticTag
                logger.debug(
                    "got '%s' for '%s' with 'high' confidence" % (
                            semanticTag, newTerm))

            elif (confidence == "good"):
                goodResult[propertyValue] = semanticTag
                logger.debug(
                    "got '%s' for '%s' with 'good' confidence" % (
                            semanticTag, newTerm))

            else:
                logger.debug(
                    "Ignoring '%s' for '%s' since confidence is '%s'" % (
                            semanticTag, newTerm, confidence))

            # if we have a low confidence, don't take the results
            # else: #  medium/low

    # HINT: is useful?
    result['type'] = category

    # TODO: check if the annotation is useful (eg throw away GAZ for a specie)

    # TODO: is not clear if I have more than one result. For what I understand
    # or I have a result or not
    if len(highResult) > 0:
        result['confidence'] = 'High'
        for value in highResult:
            result['text'] = value
            result['ontologyTerms'] = highResult[value]
            return result

    if len(goodResult) > 0:
        result['confidence'] = 'Good'
        for value in goodResult:
            result['text'] = value
            result['ontologyTerms'] = goodResult[value]
            return result

    # no results is returned with low or medium confidence
    logger.warn("No result returned for %s" % (newTerm))


def get_taxonID_by_scientific_name(scientific_name):
    # define URL
    url = urllib.parse.urljoin(
        TAXONOMY_URL,
        urllib.parse.quote("scientific-name/%s" % (scientific_name)))

    # debug
    logger.debug("Searching %s" % (url))

    response = requests.get(url)

    logger.debug(response)

    if response.status_code != 200:
        logger.error("No data retrieved for %s" % (scientific_name))
        return None

    # read results
    results = response.json()

    if len(results) > 1:
        logger.warn(
            "%s results found for %s" % (len(results), scientific_name))

    taxonId = int(results[0]['taxId'])

    logger.debug("Got taxonId %s for %s" % (taxonId, scientific_name))

    return taxonId
