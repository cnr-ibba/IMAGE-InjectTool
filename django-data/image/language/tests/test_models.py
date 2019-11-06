#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 21 15:11:55 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from uid.models import DictCountry

from ..models import SpecieSynonym


class SpecieSynonymTest(TestCase):
    fixtures = [
        "uid/dictcountry",
        "language/dictspecie",
        "language/speciesynonym"
    ]

    def setUp(self):
        # setting languages
        self.italy = DictCountry.objects.get(label="Italy")
        self.england = DictCountry.objects.get(label="United Kingdom")

    def test_check_synonyms(self):
        """Check for synonym in my language"""

        qs = SpecieSynonym.check_synonyms(["Cattle"], self.england)
        self.assertEqual(len(qs), 1)

        # search for bos taurus in italian language (map to default)
        qs = SpecieSynonym.check_synonyms(["Cattle"], self.italy)
        self.assertEqual(len(qs), 1)

        # check that I got the default english term for italy
        test = qs.first()
        self.assertEqual(test.language.label, "United Kingdom")

        # search for bos taurus in italian language (no map)
        qs = SpecieSynonym.check_synonyms(["Mucca"], self.italy)
        self.assertEqual(len(qs), 0)

    def test_check_synonyms_nospaces(self):
        """Check for synonym in my language, no matters spaces"""

        # search for a term with spaces
        qs = SpecieSynonym.check_synonyms(
            ["Sheep (domestic)"], self.england)
        self.assertEqual(len(qs), 1)

        # search for a term without spaces
        qs = SpecieSynonym.check_synonyms(
            ["Sheep(domestic)"], self.england)

        self.assertEqual(len(qs), 1)

    def test_check_specie_by_synonym(self):
        """test if a specie has a synonym"""

        self.assertTrue(
            SpecieSynonym.check_specie_by_synonym(
                "Cattle", self.england))

        self.assertTrue(
            SpecieSynonym.check_specie_by_synonym(
                "Cattle", self.italy))

        # no map for this word
        self.assertFalse(
            SpecieSynonym.check_specie_by_synonym(
                "Mucca", self.italy))

    def test_check_specie_by_synonym_nospaces(self):
        """test if a specie has a synonym, no matters spaces"""

        self.assertTrue(
            SpecieSynonym.check_specie_by_synonym(
                "Sheep (domestic)", self.england))

        self.assertTrue(
            SpecieSynonym.check_specie_by_synonym(
                "Sheep(domestic)", self.england))
