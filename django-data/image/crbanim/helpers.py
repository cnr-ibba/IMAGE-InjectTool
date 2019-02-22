#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 21 15:37:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import csv
import logging

from collections import defaultdict

from common.constants import LOADED, ERROR
from image_app.models import DictSpecie, DictSex

# Get an instance of a logger
logger = logging.getLogger(__name__)


# A class to deal with cryoweb import errors
class CRBAnimImportError(Exception):
    pass


class CRBAnimReader():
    def __init__(self):
        self.data = None
        self.header = None
        self.dialect = None
        self.items = None

    def read_file(self, filename):
        """Read crb anim files and set tit to class attribute"""

        with open(filename, newline='') as csvfile:
            self.dialect = csv.Sniffer().sniff(csvfile.read(2048))
            csvfile.seek(0)
            reader = csv.reader(csvfile, self.dialect)
            self.header = next(reader)
            self.data = list(reader)

        self.items = self.eval_columns()

    def eval_columns(self):
        """define a set from column data"""

        # target_columns = ['sex', 'species_latin_name', 'breed_name']
        target_columns = self.header

        items = defaultdict(list)

        for line in self.data:
            for column in target_columns:
                idx = self.header.index(column)
                items[column].append(line[idx])

        # now get a set of object
        for column in target_columns:
            items[column] = set(items[column])

        return items

    def print_line(self, num):
        """print a record with its column names"""

        for i, column in enumerate(self.header):
            logger.debug("%s: %s" % (column, self.data[num][i]))

    def __check_items(self, item_set, model, column):
        """General check of CRBanim items into database"""

        not_found = []

        for item in item_set:
            # check for species in database
            if not model.objects.filter(label=item).exists():
                not_found.append(item)

        if len(not_found) == 0:
            return True

        else:
            logger.error(
                "Those %s are not present in UID database:" % (column))
            logger.error(not_found)

            return False

    # a function to detect if crbanim species are in UID database or not
    # HINT: crbanim species are already in the form required from DictSpecies
    # tables, no need to search for language
    def check_species(self):
        """Check if all species are defined in UID DictSpecies"""

        column = 'species_latin_name'

        return self.__check_items(self.items[column], DictSpecie, column)

    # check that dict sex table contains data
    def check_sex(self):
        """check that dict sex table contains data"""

        # item.sex are in uppercase
        column = 'sex'
        item_set = [item.lower() for item in self.items[column]]

        return self.__check_items(item_set, DictSex, column)


def upload_crbanim(submission):
    # debug
    logger.info("Importing from CRB-Anim file")

    # this is the full path in docker container
    fullpath = submission.get_uploaded_file_path()

    # read submission data
    reader = CRBAnimReader()
    reader.read_file(fullpath)

    # start data loading
    try:
        # check for species and sex like cryoweb does
        if not reader.check_sex():
            raise CRBAnimImportError("You have to upload DictSex data")

        if not reader.check_species():
            raise CRBAnimImportError(
                "Some species are not loaded in UID database")

    except Exception as exc:
        # save a message in database
        submission.status = ERROR
        submission.message = "Error in importing data: %s" % (str(exc))
        submission.save()

        # debug
        logger.error("error in importing from crbanim: %s" % (exc))
        logger.exception(exc)

        return False

    else:
        message = "CRBAnim import completed for submission: %s" % (
            submission.id)

        submission.message = message
        submission.status = LOADED
        submission.save()

    logger.info("Import from CRBAnim is complete")

    return True
