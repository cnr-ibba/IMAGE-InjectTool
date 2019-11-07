#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 16:31:45 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import xlrd
import logging
import datetime

from collections import defaultdict, namedtuple

from common.constants import ACCURACIES
from uid.helpers import FileDataSourceMixin
from uid.models import DictSex, DictCountry

from .exceptions import ExcelImportError

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


class ExcelTemplateReader(FileDataSourceMixin):
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

    def get_sheet_records(self, sheet_name):
        """Generic functions to iterate on excel records"""

        # this is the sheet I need
        sheet = self.book.sheet_by_name(sheet_name)

        # now get columns to create a collection objects
        header = sheet.row_values(0)

        column_idxs = {}

        # get the column index I need
        for column in TEMPLATE_COLUMNS[sheet_name]:
            try:
                idx = header.index(column)

            except ValueError as e:
                logger.error(e)
                raise ExcelImportError(
                    "Column '%s' not found in '%s' sheet" % (
                        column, sheet_name))

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

            # replace all empty  occurences in a list
            data = [None if col in [""]
                    else col for col in data]

            # stripping columns
            data = [col.strip() if type(col) is str
                    else col for col in data]

            # treat integers as integers
            data = [int(col) if type(col) is float and col.is_integer()
                    else col for col in data]

            # fix date fields. Search for 'date' in column names
            date_idxs = [column_idxs[column] for column in columns if
                         'date' in column]

            # fix date objects using datetime, as described here:
            # https://stackoverflow.com/a/13962976/4385116
            for idx in date_idxs:
                if not data[idx]:
                    continue

                data[idx] = datetime.datetime(
                    *xlrd.xldate_as_tuple(
                        data[idx],
                        self.book.datemode
                    )
                )

            # get a new object
            record = Record._make(data)

            yield record

    def get_breed_records(self):
        """Iterate among breeds record"""

        # this is the sheet I need
        sheet_name = "breed"
        return self.get_sheet_records(sheet_name)

    def get_animal_records(self):
        """Iterate among animal records"""

        # this is the sheet I need
        sheet_name = "animal"
        return self.get_sheet_records(sheet_name)

    def get_sample_records(self):
        """Iterate among sample records"""

        # this is the sheet I need
        sheet_name = "sample"
        return self.get_sheet_records(sheet_name)

    def get_animal_from_sample(self, record):
        """get an animal record from a sample record"""

        animals = [
            animal for animal in self.get_animal_records() if
            animal.animal_id_in_data_source == record.animal_id_in_data_source
        ]

        # animal is supposed to be unique
        if len(animals) != 1:
            raise ExcelImportError(
                "Can't determine a unique animal from '%s' record data" %
                (record))

        return animals[0]

    def get_breed_from_animal(self, record):
        """Get a breed record from an animal record"""

        breeds = [
            breed for breed in self.get_breed_records()
            if breed.supplied_breed == record.breed and
            breed.species == record.species]

        # breed is supposed to be unique, from UID constraints. However
        # I could place the same breed name for two countries. In that case,
        # I cant derive a unique breed from users data
        if len(breeds) != 1:
            raise ExcelImportError(
                "Can't determine a unique breed for '%s:%s' from user data" %
                (record.breed, record.species))

        return breeds[0]

    def check_species(self, country):
        """Check if all species are defined in UID DictSpecies. If not,
        create dictionary term"""

        column = 'species'
        item_set = set([breed.species for breed in self.get_breed_records()])

        # call FileDataSourceMixin.check_species
        return super().check_species(column, item_set, country, create=True)

    def check_species_in_animal_sheet(self):
        """Check if all animal species are defined in breed sheet"""

        check = True
        not_found = []

        reference_set = set(
            [breed.species for breed in self.get_breed_records()])

        test_set = set(
            [animal.species for animal in self.get_animal_records()])

        for specie in test_set:
            if specie not in reference_set:
                check = False
                not_found.append(specie)

        return check, not_found

    def check_sex(self):
        """Check that all sex records are present in database"""

        column = 'sex'
        item_set = set([animal.sex for animal in self.get_animal_records()])

        # call FileDataSourceMixin.check_items
        return self.check_items(item_set, DictSex, column)

    def check_countries(self):
        """Check that all efabis countries are present in database"""

        column = "efabis_breed_country"
        item_set = set([breed.efabis_breed_country for
                        breed in self.get_breed_records()])

        # call FileDataSourceMixin.check_items
        return self.check_items(item_set, DictCountry, column)

    def __check_accuracy(self, item_set):
        """A generic method to test for accuracies"""

        # a list of not found terms and a status to see if something is missing
        # or not
        not_found = []
        result = True

        for item in item_set:
            try:
                ACCURACIES.get_value_by_desc(item)

            except KeyError:
                logger.warning("accuracy level '%s' not found" % (item))
                not_found.append(item)

        if len(not_found) != 0:
            result = False

        return result, not_found

    def check_accuracies(self):
        """Check accuracy specified in table"""

        item_set = set([animal.birth_location_accuracy
                        for animal in self.get_animal_records()])

        # test for accuracy in animal table
        result_animal, not_found_animal = self.__check_accuracy(item_set)

        item_set = set([sample.collection_place_accuracy
                        for sample in self.get_sample_records()])

        # test for accuracy in sample table
        result_sample, not_found_sample = self.__check_accuracy(item_set)

        # merge two results
        check = result_animal and result_sample
        not_found = set(not_found_animal + not_found_sample)

        if check is False:
            logger.error(
                    "Couldnt' find those accuracies in constants:")
            logger.error(not_found)

        return check, not_found
