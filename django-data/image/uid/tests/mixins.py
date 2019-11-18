#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 15:57:10 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from common.tests import DataSourceMixinTestCase as CommonDataSourceMixinTest

from ..models import (
    db_has_data, Animal, Sample, Submission, DictCountry, DictSpecie, DictSex,
    Person)


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


class FileReaderMixinTestCase:
    """A class to deal with common text between CRBAnimReader and
    ExcelTemplateReader"""

    def test_check_species(self):
        """Test check species method"""

        # get a country
        country = DictCountry.objects.get(label="United Kingdom")

        check, not_found = self.reader.check_species(country)

        self.assertTrue(check)
        self.assertEqual(len(not_found), 0)

        # changing species set
        DictSpecie.objects.filter(label='Capra hircus').delete()

        check, not_found = self.reader.check_species(country)

        # the read species are not included in fixtures
        self.assertFalse(check)
        self.assertGreater(len(not_found), 0)

    def test_check_sex(self):
        """Test check sex method"""

        check, not_found = self.reader.check_sex()

        self.assertTrue(check)
        self.assertEqual(len(not_found), 0)

        # changing sex set
        DictSex.objects.filter(label='female').delete()

        check, not_found = self.reader.check_sex()

        # the read species are not included in fixtures
        self.assertFalse(check)
        self.assertGreater(len(not_found), 0)

    def test_check_countries(self):
        "Testing country method"""

        # assert countries are present
        check, not_found = self.reader.check_countries()

        self.assertTrue(check)
        self.assertEqual(len(not_found), 0)

        # remove a country from UID
        DictCountry.objects.filter(label="Italy").delete()

        check, not_found = self.reader.check_countries()

        self.assertFalse(check)
        self.assertGreater(len(not_found), 0)


# a mixin to correctly instantiate a person object in order to get
# a biosample json for test data
class PersonMixinTestCase(object):
    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        # now fix person table
        person = Person.objects.get(user__username="test")
        person.affiliation_id = 1
        person.role_id = 1
        person.initials = "T"
        person.save()
