#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 15:47:23 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from image_app.models import DictCountry, DictSpecie

from ..helpers import check_species_synonyms
from ..models import SpecieSynonym


class CheckSpecie(TestCase):
    fixtures = [
        'image_app/dictcountry',
        'language/dictspecie',
        'language/speciesynonym'
    ]

    def test_check_species_synonyms(self):
        """Testing species and synonyms"""

        country = DictCountry.objects.get(label="Italy")

        # search for words, where one synonym is not present
        words = ["Cattle", "Pecora"]

        # check result
        result = check_species_synonyms(words, country)

        # If I don't find a synonym, I will return False
        self.assertFalse(result)

        # now I have a synonym without species
        synonym = SpecieSynonym.objects.get(word="Pecora")
        self.assertEqual(synonym.language, country)
        self.assertIsNone(synonym.dictspecie)

        # if I check again, I will have False again
        result = check_species_synonyms(words, country)
        self.assertFalse(result)

        # get a species and update
        sheep = DictSpecie.objects.get(label="Ovis aries")
        synonym.dictspecie = sheep
        synonym.save()

        # now I have True
        result = check_species_synonyms(words, country)
        self.assertTrue(result)
