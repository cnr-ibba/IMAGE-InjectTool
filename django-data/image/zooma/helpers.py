#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 15:49:04 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Functions adapted from Jun Fan misc.py and use_zooma.py python scripts
"""

import re

import requests


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

    # main production server
    host = "https://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate?propertyValue="+newTerm

    # test zooma server
    # host = "http://snarf.ebi.ac.uk:8480/spot/zooma/v2/api/services/annotate?propertyValue="+newTerm
    # add filter: configure datasource and ols libraries
    host += "&filter=required:[ena],ontologies:[efo,uberon,obi,NCBITaxon,lbo,pato,gaz]"  #according to IMAGE ruleset, only these ontology libraries are allowed in the ruleset, so not search others, gaz is for countries

    category = from_camel_case(category)

    if category == "species":  # necessary if
        category = "organism"

    highResult = {}
    goodResult = {}
    result = {}

    request = requests.get(host)

    # print (json.dumps(request.json(), indent=4, sort_keys=True))

    for elem in request.json():
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

            elif (confidence == "good"):
                goodResult[propertyValue] = semanticTag

            # if we have a low confidence, don't take the results
            # else: #  medium/low

    result['type'] = category

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
