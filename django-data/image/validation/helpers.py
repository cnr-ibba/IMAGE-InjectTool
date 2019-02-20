#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 16:15:35 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from image_validation import validation
from image_validation.static_parameters import ruleset_filename as \
    IMAGE_RULESET


class MetaDataValidation():
    """A class to deal with IMAGE-ValidationTool ruleset objects"""

    ruleset = None

    def __init__(self, ruleset_filename=IMAGE_RULESET):
        self.read_in_ruleset(ruleset_filename)

    def read_in_ruleset(self, ruleset_filename):
        self.ruleset = validation.read_in_ruleset(ruleset_filename)

    def check_usi_structure(self, data):
        """Check data against USI rules"""

        return validation.check_usi_structure(data)

    def check_ruleset(self):
        """Check ruleset"""

        return validation.check_ruleset(self.ruleset)

    def check_duplicates(self, data):
        """Check duplicates in data"""

        return validation.check_duplicates(data)

    def validate(self, record):
        """Check attributes for record"""

        return self.ruleset.validate(record)
