#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 10:44:54 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import xlrd
import logging

from collections import defaultdict, namedtuple

from common.constants import ERROR, LOADED
from image_app.models import (
    DictBreed, DictCountry, DictSpecie, DictSex, Name)
from language.helpers import check_species_synonyms
from submissions.helpers import send_message
from validation.helpers import construct_validation_message

# Get an instance of a logger
logger = logging.getLogger(__name__)

# defining the template columns in need for data import
TEMPLATE_COLUMNS = {
    'breed': [
        'Supplied breed',
        # 'Mapped breed',
        # 'Mapped breed ontology library',
        # 'Mapped breed ontology accession',
        'EFABIS Breed country',
        'Species',
        # 'Species ontology library',
        # 'Species ontology accession'
    ],
    'animal': [
        'Animal id in data source',
        'Animal description',
        'Alternative animal ID',
        'Father id in data source',
        'Mother id in data source',
        'Breed',
        'Species',
        'Sex',
        'Birth date',
        'Birth location',
        'Birth location longitude',
        'Birth location latitude',
        'Birth location accuracy'
    ],
    'sample': [
        'Sample id in data source',
        'Alternative sample ID',
        'Sample description',
        'Animal id in data source',
        'Specimen collection protocol',
        'availability',
        'Collection date',
        'Collection place latitude',
        'Collection place longitude',
        'Collection place',
        'Collection place accuracy',
        'Organism part',
        'Developmental stage',
        'Physiological stage',
        'Animal age at collection',
        'Sample storage',
        'Sample storage processing',
        'Sampling to preparation interval'
    ]
}


# A class to deal with template import errors
class ExcelImportError(Exception):
    pass


class ExcelTemplate():
    """A class to read template excel files"""

    def __init__(self):
        # read xls file and track it
        self.book = None
        self.sheet_names = []

    def read_file(self, filename):
        # read xls file and track it
        self.book = xlrd.open_workbook(filename)
        self.sheet_names = self.book.sheet_names()

    def check_sheets(self):
        """Test for the minimal sheets required to upload data"""

        not_found = []

        for sheet_name in TEMPLATE_COLUMNS.keys():
            if sheet_name not in self.sheet_names:
                not_found.append(sheet_name)
                logger.error(
                    "required sheet {name} not found in template".format(
                        name=sheet_name)
                )

        if len(not_found) > 0:
            return False, not_found

        else:
            logger.debug("This seems to be a valid Template file")
            return True, not_found

    def check_columns(self):
        """Test for minimal column required for template load"""

        not_found = defaultdict(list)

        for sheet_name in TEMPLATE_COLUMNS.keys():
            # get a sheet from xls workbook
            sheet = self.book.sheet_by_name(sheet_name)

            # get header from sheet
            header = sheet.row_values(0)

            for column in TEMPLATE_COLUMNS[sheet_name]:
                if column not in header:
                    not_found[sheet_name].append(column)
                    logger.error(
                        "required column {column} not found in sheet "
                        "{sheet_name}".format(
                            sheet_name=sheet_name,
                            column=column)
                    )

        if len(not_found) > 0:
            return False, not_found

        else:
            logger.debug("This seems to be a valid Template file")
            return True, not_found

    def __get_sheet_records(self, sheet_name):
        """Generic functions to iterate on excel records"""

        # this is the sheet I need
        sheet = self.book.sheet_by_name(sheet_name)

        # now get columns to create a collection objects
        header = sheet.row_values(0)

        column_idxs = {}

        # get the column index I need
        for column in TEMPLATE_COLUMNS[sheet_name]:
            idx = header.index(column)
            column_idxs[column.lower().replace(" ", "_")] = idx

        # get new column names
        columns = column_idxs.keys()

        # create a namedtuple object
        Record = namedtuple(sheet_name.capitalize(), columns)

        # iterate over record, mind the header column
        for i in range(1, sheet.nrows):
            # get a row from excel file
            row = sheet.row_values(i)

            # get the data I need
            data = [row[column_idxs[column]] for column in columns]

            # get a new object
            record = Record._make(data)

            yield record

    def get_breed_records(self):
        """Iterate among breeds record"""

        # this is the sheet I need
        sheet_name = "breed"
        return self.__get_sheet_records(sheet_name)

    def get_animal_records(self):
        """Iterate among animal records"""

        # this is the sheet I need
        sheet_name = "animal"
        return self.__get_sheet_records(sheet_name)

    def get_sample_records(self):
        """Iterate among sample records"""

        # this is the sheet I need
        sheet_name = "sample"
        return self.__get_sheet_records(sheet_name)

    # TODO: identical to CRBanim move in a common mixin
    def __check_items(self, item_set, model, column):
        """General check of Template items into database"""

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

    # TODO: nearly identical to CRBanim move in a common mixin
    def check_species(self, country):
        """Check if all species are defined in UID DictSpecies"""

        column = 'species'
        item_set = set([breed.species for breed in self.get_breed_records()])

        check, not_found = self.__check_items(
            item_set, DictSpecie, column)

        if check is False:
            # try to check in dictionary table
            logger.info("Searching for %s in dictionary tables" % (not_found))

            # if this function return True, I found all synonyms
            if check_species_synonyms(not_found, country) is True:
                logger.info("Found %s in dictionary tables" % not_found)

                # return True and an empty list for check and not found items
                return True, []

        # if I arrive here, there are species that I couldn't find
        logger.error("Couldnt' find those species in dictionary tables:")
        logger.error(not_found)

        return check, not_found

    # TODO: nearly identical to CRBanim move in a common mixin
    def check_sex(self):
        """Check that all sex records are present in database"""

        column = 'sex'
        item_set = set([animal.sex for animal in self.get_animal_records()])

        return self.__check_items(item_set, DictSex, column)


def fill_uid_breeds(submission_obj, template):
    """Fill DictBreed from a excel record"""

    logger.info("fill_uid_breeds() started")

    # ok get languages from submission (useful for translation)
    language = submission_obj.gene_bank_country.label

    # iterate among excel template
    for record in template.get_breed_records():
        # TODO: move this in a helper module (image_app.helpers?)
        # get a DictSpecie object. Species are in latin names, but I can
        # find also a common name in translation tables
        try:
            specie = DictSpecie.objects.get(label=record.species)

        except DictSpecie.DoesNotExist:
            logger.info("Search %s in synonyms" % (record.species))
            # search for language synonym (if I arrived here a synonym should
            # exists)
            specie = DictSpecie.get_by_synonym(
                synonym=record.species,
                language=language)

        # get country for breeds. Ideally will be the same of submission,
        # however, it could be possible to store data from other contries
        country, created = DictCountry.objects.get_or_create(
            label=record.efabis_breed_country)

        # I could create a country from a v_breed_specie instance. That's
        # ok, maybe I could have a lot of breed from different countries and
        # a few organizations submitting them
        if created:
            logger.info("Created %s" % country)

        else:
            logger.debug("Found %s" % country)

        breed, created = DictBreed.objects.get_or_create(
            supplied_breed=record.supplied_breed,
            specie=specie,
            country=country)

        if created:
            logger.info("Created %s" % breed)

        else:
            logger.debug("Found %s" % breed)

    logger.info("fill_uid_breeds() completed")


def fill_uid_names(submission_obj, template):
    """fill Names table from crbanim record"""

    # debug
    logger.info("called fill_uid_names()")

    # iterate among excel template
    for record in template.get_animal_records():
        # in the same record I have the sample identifier and animal identifier
        # a name record for animal
        animal_name, created = Name.objects.get_or_create(
            name=record.animal_id_in_data_source,
            submission=submission_obj,
            owner=submission_obj.owner)

        if created:
            logger.debug("Created animal name %s" % animal_name)

        else:
            logger.debug("Found animal name %s" % animal_name)

    # iterate among excel template
    for record in template.get_sample_records():
        # name record for sample
        sample_name, created = Name.objects.get_or_create(
            name=record.sample_id_in_data_source,
            submission=submission_obj,
            owner=submission_obj.owner)

        if created:
            logger.debug("Created sample name %s" % sample_name)

        else:
            logger.debug("Found sample name %s" % sample_name)

    logger.info("fill_uid_names() completed")


def fill_uid_animals(submission_obj, template):
    # debug
    logger.info("called fill_uid_animals()")

    # debug
    logger.info("fill_uid_animals() completed")


def fill_uid_samples(submission_obj, template):
    # debug
    logger.info("called fill_uid_samples()")

    # debug
    logger.info("fill_uid_samples() completed")


def upload_template(submission_obj):
    # debug
    logger.info("Importing from Excel template file")

    # this is the full path in docker container
    fullpath = submission_obj.get_uploaded_file_path()

    # read submission data
    reader = ExcelTemplate()
    reader.read_file(fullpath)

    # start data loading
    try:
        # check for species and sex in a similar way as cryoweb does
        # TODO: identical to CRBanim. Move to a mixin
        check, not_found = reader.check_sex()

        if not check:
            message = (
                "Not all Sex terms are loaded into database: "
                "check for %s in your dataset" % (not_found))

            raise ExcelImportError(message)

        check, not_found = reader.check_species(
            submission_obj.gene_bank_country)

        if not check:
            raise ExcelImportError(
                "Some species are not loaded in UID database: "
                "%s" % (not_found))

        # BREEDS
        fill_uid_breeds(submission_obj, reader)

        # NAME
        fill_uid_names(submission_obj, reader)

        # ANIMALS
        fill_uid_animals(submission_obj, reader)

        # SAMPLES
        fill_uid_samples(submission_obj, reader)

    except Exception as exc:
        # set message:
        message = "Error in importing data: %s" % (str(exc))

        # save a message in database
        submission_obj.status = ERROR
        submission_obj.message = message
        submission_obj.save()

        # send async message
        send_message(submission_obj)

        # debug
        logger.error("Error in importing from Template: %s" % (exc))
        logger.exception(exc)

        return False

    else:
        message = "Template import completed for submission: %s" % (
            submission_obj.id)

        submission_obj.message = message
        submission_obj.status = LOADED
        submission_obj.save()

        # send async message
        send_message(
            submission_obj,
            validation_message=construct_validation_message(submission_obj))

    logger.info("Import from Template is complete")

    return True
