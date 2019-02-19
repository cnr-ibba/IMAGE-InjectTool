#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 13:34:43 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase

from image_app.models import DictBreed, DictCountry, DictSpecie, DictUberon

from ..tasks import (
    AnnotateBreeds, AnnotateCountries, AnnotateSpecies, AnnotateUberon)


class TestAnnotateBreeds(TestCase):
    """A class to test annotate breeds"""

    fixtures = [
        "image_app/dictbreed",
        "image_app/dictcountry",
        "image_app/dictspecie"
    ]

    def setUp(self):
        self.my_task = AnnotateBreeds()

        # get a breed object
        breed = DictBreed.objects.get(pk=1)

        # erase attributes
        breed.mapped_breed = None
        breed.mapped_breed_term = None
        breed.confidence = None
        breed.save()

    @patch("zooma.tasks.annotate_breed")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)


class TestAnnotateCountries(TestCase):
    """A class to test annotate countries"""

    fixtures = [
        "image_app/dictcountry",
    ]

    def setUp(self):
        self.my_task = AnnotateCountries()

        # get a country object
        country = DictCountry.objects.get(pk=1)

        # erase attributes
        country.term = None
        country.confidence = None
        country.save()

    @patch("zooma.tasks.annotate_country")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)


class TestAnnotateSpecies(TestCase):
    """A class to test annotate species"""

    fixtures = [
        "image_app/dictspecie",
    ]

    def setUp(self):
        self.my_task = AnnotateSpecies()

        # get a specie object
        specie = DictSpecie.objects.get(pk=1)

        # erase attributes
        specie.term = None
        specie.confidence = None
        specie.save()

    @patch("zooma.tasks.annotate_specie")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)


class TestAnnotateUberon(TestCase):
    """A class to test annotate uberon"""

    fixtures = [
        "image_app/dictuberon",
    ]

    def setUp(self):
        self.my_task = AnnotateUberon()

        # get a specie object
        part = DictUberon.objects.get(pk=1)

        # erase attributes
        part.term = None
        part.confidence = None
        part.save()

    @patch("zooma.tasks.annotate_uberon")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)
