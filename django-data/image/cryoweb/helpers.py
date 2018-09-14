#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 14 10:28:39 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from cryoweb.models import VBreedSpecies
from language.models import SpecieSynonim

# Get an instance of a logger
logger = logging.getLogger(__name__)


# a function to detect if cryoweb species have synonims or not
def check_species(language):
    """Check specie for a language, ie: check_species(language='Germany').
    Language is image_app.models.DictCountry.label"""

    # get all species using view
    species = VBreedSpecies.get_all_species()

    # get a queryset for each
    synonims = SpecieSynonim.objects.filter(
        word__in=species, language__label=language)

    # HINT: is this state useful?
    # check that numbers are equal
    if len(species) == synonims.count():
        logger.debug("Each species has a synonim in %s language" % (language))
        return True

    elif len(species) > synonims.count():
        logger.warning("Some species haven't a synonim!")
        return False

    # may I see this case? For instance when filling synonims?
    else:
        raise NotImplementedError("Not implemented")
