#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 13:10:15 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import json
import logging

from zooma.helpers import to_camel_case

# Get an instance of a logger
logger = logging.getLogger(__name__)

# need to derive the absolute path of sample ruleset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sample_path = os.path.join(
    BASE_DIR, "metadata/rulesets/sample_ruleset.json")

# read data from json file
with open(sample_path) as handle:
    sample_data = json.load(handle)

# get rule_groups from dictionary
rule_groups = sample_data.get('rule_groups')

# use the same mapping keys between ruleset and sections defined by Jun
key2key = {
    'standard': 'common',
    'organism': 'animal',
    'specimen from organism': 'sample'}

# scan and search mandatory fields for each rule group
mandatory_fields = {}
optional_fields = {}
recommended_fields = {}

# reading keys and set mandatory and optional fields
for key1, key2 in key2key.items():
    mandatory_fields[key2] = {}
    optional_fields[key2] = {}
    recommended_fields[key2] = {}

    for group in rule_groups:
        # deal with the list as the current key1
        if group['name'] == key1:
            # get rules from group dictionary
            for field in group.get('rules'):
                # use the camel case convention for names
                name = to_camel_case(field['Name'])

                # track mandatory fields in a dictionary
                if field['Required'] == 'mandatory':
                    mandatory_fields[key2][name] = field

                elif field['Required'] == 'optional':
                    optional_fields[key2][name] = field

                elif field['Required'] == 'recommended':
                    recommended_fields[key2][name] = field

                else:
                    logger.warn("Ignoring %s" % field)


# defining classes in order to validate Animals or samples
class CommonValidator():
    def __init__(self, mandatory_fields=mandatory_fields):
        self.mandatory_fields = mandatory_fields

    def check_minimal(self, data):
        """Check minimal requirement for biosample"""

        status = True

        for key in ['alias', 'title', 'releaseDate', 'taxonId']:
            if key not in data.keys():
                logger.error("key %s not found in %s" % (key, data))
                status = False

        return status

    def check_mandatory(self, data):
        """check common fields in attribute fields"""

        status = True

        for key in self.mandatory_fields['common'].keys():
            if key not in data['attributes']:
                logger.error(
                    "key %s not found in attributes %s" % (
                        key, data['attributes']))
                status = False

        return status


class AnimalValidator(CommonValidator):
    def check_mandatory(self, data):
        """check animal fields in attribute fields"""

        status = super().check_mandatory(data)

        for key in self.mandatory_fields['animal'].keys():
            if key not in data['attributes']:
                logger.error(
                    "key %s not found in attributes %s" % (
                        key, data['attributes']))
                status = False

        return status


class SampleValidator(CommonValidator):
    def check_mandatory(self, data):
        """check animal fields in attribute fields"""

        status = super().check_mandatory(data)

        for key in self.mandatory_fields['sample'].keys():
            if key not in data['attributes']:
                logger.error(
                    "key %s not found in attributes %s" % (
                        key, data['attributes']))
                status = False

        return status
