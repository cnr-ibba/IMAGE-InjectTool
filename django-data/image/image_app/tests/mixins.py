#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 15:57:10 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from common.tests import DataSourceMixinTestCase as CommonDataSourceMixinTest

from ..models import db_has_data, Animal, Sample, Submission


class DataSourceMixinTestCase(CommonDataSourceMixinTest):
    # defining attribute classes
    submission_model = Submission

    def upload_datasource(self, message):
        """test upload data from DatsSource"""

        super(DataSourceMixinTestCase, self).upload_datasource(message)

        # assert data into database
        self.assertTrue(db_has_data())
        self.assertTrue(Animal.objects.exists())
        self.assertTrue(Sample.objects.exists())

    def check_errors(self, my_check, message):
        """Common stuff for cehcking error in file loading"""

        super(DataSourceMixinTestCase, self).check_errors(my_check, message)

        # assert data into database
        self.assertFalse(db_has_data())
        self.assertFalse(Animal.objects.exists())
        self.assertFalse(Sample.objects.exists())
