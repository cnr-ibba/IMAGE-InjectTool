#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 12:41:05 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Common functions in uid

"""

import re
import logging

from language.helpers import check_species_synonyms

from .models import Animal, Sample, DictSpecie

# Get an instance of a logger
logger = logging.getLogger(__name__)

# a pattern to correctly parse aliases
ALIAS_PATTERN = re.compile(r"IMAGE([AS])([0-9]+)")


def parse_image_alias(alias):
    """Parse alias and return table and pk"""

    match = re.search(ALIAS_PATTERN, alias)

    if not match:
        raise Exception("Cannot deal with '%s'" % (alias))

    letter, padded_pk = match.groups()
    table, pk = None, None

    if letter == "A":
        table = "Animal"

    elif letter == "S":
        table = "Sample"

    pk = int(padded_pk)

    return table, pk


def get_model_object(table, pk):
    """Get a model object relying on table name (Sample/Alias) and pk"""

    # get sample object
    if table == "Animal":
        sample_obj = Animal.objects.get(pk=pk)

    elif table == "Sample":
        sample_obj = Sample.objects.get(pk=pk)

    else:
        raise Exception("Unknown table '%s'" % (table))

    return sample_obj


class FileDataSourceMixin():
    """A class to deal with common operation between Template and CRBanim
    files"""

    def check_items(self, item_set, model, column):
        """General check of DataSource items into database"""

        # a list of not found terms and a status to see if something is missing
        # or not
        not_found = []
        result = True

        for item in item_set:
            # check for species in database
            if not model.objects.filter(label=item).exists():
                not_found.append(item)

        if len(not_found) != 0:
            result = False
            logger.warning(
                "Those %s are not present in UID database:" % (column))
            logger.warning(not_found)

        return result, not_found

    def check_species(self, column, item_set, country, create=False):
        """Check if all species are defined in UID DictSpecies. Create
        dictionary term if create is True and species is not found"""

        check, not_found = self.check_items(
            item_set, DictSpecie, column)

        if check is False:
            # try to check in dictionary table
            logger.info("Searching for %s in dictionary tables" % (not_found))

            # if this function return True, I found all synonyms
            if check_species_synonyms(not_found, country, create) is True:
                logger.info("Found %s in dictionary tables" % not_found)

                # return True and an empty list for check and not found items
                return True, []

            else:
                # if I arrive here, there are species that I couldn't find
                logger.error(
                    "Couldnt' find those species in dictionary tables:")
                logger.error(not_found)

        return check, not_found


def get_or_create_obj(model, **kwargs):
    """Generic method to create or getting a model object"""

    instance, created = model.objects.get_or_create(**kwargs)

    if created:
        logger.info("Created '%s'" % instance)

    else:
        logger.debug("Found '%s'" % instance)

    return instance


def update_or_create_obj(model, **kwargs):
    """Generic method to create or getting a model object"""

    instance, created = model.objects.update_or_create(**kwargs)

    if created:
        logger.debug("Created '%s'" % instance)

    else:
        logger.debug("Updating '%s'" % instance)

    return instance
