#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 10:44:54 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import xlrd
import logging

from collections import defaultdict

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


def upload_template(submission_obj):
    pass
