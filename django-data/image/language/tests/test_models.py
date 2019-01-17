#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 21 15:11:55 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from image_app.models import DictCountry

from ..models import SpecieSynonim


class SpecieSynonimTest(TestCase):
    fixtures = [
        "image_app/dictcountry",
        "language/dictspecie",
        "language/speciesynonim"
    ]

    def setUp(self):
        # setting languages
        self.italy = DictCountry.objects.get(label="Italy")
        self.england = DictCountry.objects.get(label="United Kingdom")

    def test_check_synonims(self):
        """Check for synonym in my language"""

        qs = SpecieSynonim.check_synonims(["Cattle"], self.england)
        self.assertEqual(len(qs), 1)

        # search for bos taurus in italian language (map to default)
        qs = SpecieSynonim.check_synonims(["Cattle"], self.italy)
        self.assertEqual(len(qs), 1)

        # check that I got the default eglis term for italy
        test = qs.first()
        self.assertEqual(test.language.label, "United Kingdom")

        # search for bos taurus in italian language (no map)
        qs = SpecieSynonim.check_synonims(["Mucca"], self.italy)
        self.assertEqual(len(qs), 0)

    def test_check_specie_by_synonim(self):
        """If a specie has a synonim"""

        self.assertTrue(
            SpecieSynonim.check_specie_by_synonim(
                "Cattle", self.england))

        self.assertTrue(
            SpecieSynonim.check_specie_by_synonim(
                "Cattle", self.italy))

        # no map for this word
        self.assertFalse(
            SpecieSynonim.check_specie_by_synonim(
                "Mucca", self.italy))
