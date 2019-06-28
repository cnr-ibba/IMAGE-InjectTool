#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 14:01:21 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import Mock, patch


# https://github.com/testing-cabal/mock/issues/139#issuecomment-122128815
class PickableMock(Mock):
    """Provide a __reduce__ method to allow pickling mock objects"""

    def __reduce__(self):
        return (Mock, ())


class MetaDataValidationTestMixin(object):
    """Mock read_in_ruleset and check_ruleset methods"""

    def setUp(self):
        # call base instance
        super().setUp()

        # mocking up image_validation methods
        self.read_in_ruleset_patcher = patch(
            "validation.helpers.validation.read_in_ruleset")
        self.read_in_ruleset = self.read_in_ruleset_patcher.start()

        self.check_ruleset_patcher = patch(
            "validation.helpers.validation.check_ruleset")
        self.check_ruleset = self.check_ruleset_patcher.start()
        self.check_ruleset.return_value = []

        # patch check ruleset with a default value
        result = PickableMock()
        result.get_overall_status.return_value = "Pass"
        result.get_messages.return_value = []
        self.check_ruleset.return_value = result

    def tearDown(self):
        # stopping mock objects
        self.read_in_ruleset_patcher.stop()
        self.check_ruleset_patcher.stop()

        # calling base methods
        super().tearDown()
