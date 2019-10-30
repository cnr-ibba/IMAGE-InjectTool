#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 10:34:44 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import TestCase

from uid.models import Animal, Sample, DictSex

from ..helpers import (
    get_model_object, parse_image_alias, get_or_create_obj,
    update_or_create_obj)


class GetModelObjectTestCase(TestCase):
    fixtures = [
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user',
    ]

    def setUp(self):
        self.animal_id = 1
        self.sample_id = 1

    def test_get_model_object(self):

        test = get_model_object("Animal", 1)
        self.assertEqual(test.id, self.animal_id)
        self.assertIsInstance(test, Animal)

        test = get_model_object("Sample", 1)
        self.assertEqual(test.id, self.sample_id)
        self.assertIsInstance(test, Sample)

        # assert errors
        self.assertRaisesMessage(
            Exception,
            "Unknown table",
            get_model_object,
            "Name",
            1)


class ParseImageAliasTestCase(TestCase):
    fixtures = [
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user',
    ]

    def setUp(self):
        self.animal = Animal.objects.get(pk=1)
        self.sample = Sample.objects.get(pk=1)

    def test_parse_aliases(self):
        animal_alias = self.animal.biosample_alias
        sample_alias = self.sample.biosample_alias

        # test animal
        table, pk = parse_image_alias(animal_alias)

        self.assertEqual(table, "Animal")
        self.assertEqual(pk, self.animal.id)

        # test sample
        table, pk = parse_image_alias(sample_alias)

        self.assertEqual(table, "Sample")
        self.assertEqual(pk, self.sample.id)

    def test_wrong_alias(self):
        """Test a wrong alias format"""

        self.assertRaisesMessage(
            Exception,
            "Cannot deal with 'FAKEA0000123456'",
            parse_image_alias,
            "FAKEA0000123456")


class CreateOrGetTestCase(TestCase):
    fixtures = ['uid/dictsex']

    def test_get_or_create_obj(self):
        sex = get_or_create_obj(DictSex, label="male")
        self.assertIsInstance(sex, DictSex)

        sex = get_or_create_obj(DictSex, label="foo")
        self.assertIsInstance(sex, DictSex)

    def test_update_or_create_obj(self):
        sex = update_or_create_obj(DictSex, label="male", term="PATO_0000384")
        self.assertIsInstance(sex, DictSex)

        sex = update_or_create_obj(DictSex, label="foo", term="bar")
        self.assertIsInstance(sex, DictSex)
