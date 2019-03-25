#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 15:17:14 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from .models import SpecieSynonym

# Get an instance of a logger
logger = logging.getLogger(__name__)


def check_species_synonyms(words, country, create=False):
    """Check if every words is a synonym of a specie or not. If auto_create
    is true, this function will create a row in synonym table (with unkwnon
    relationship with species)"""

    # test with language.models.SpecieSynonym methods
    synonyms = SpecieSynonym.check_synonyms(words, country)

    # check that numbers are equal
    if len(words) == synonyms.count():
        logger.debug("Each species has a synonym in %s language" % (country))
        return True

    elif len(words) > synonyms.count():
        logger.warning(
            "Some species haven't a synonym for language: '%s'!" % (country))
        logger.debug("Following terms lack of synonym:")

        for word in words:
            if not SpecieSynonym.check_specie_by_synonym(word, country):
                logger.debug("%s has no specie related" % (word))

            if create is True:
                create_specie_synonym(word, country)

        # check_specie fails, since there are words not related to species
        return False

    # may I see this case? For instance when filling synonyms?
    else:
        raise NotImplementedError("Not implemented")


def create_specie_synonym(word, country):
    """add specie in speciesynonym table"""

    synonym, created = SpecieSynonym.objects.get_or_create(
        word=word,
        language=country)

    if created:
        logger.debug("Added synonym %s" % (synonym))
