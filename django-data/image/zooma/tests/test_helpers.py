#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 16:23:17 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from unittest.mock import patch

from django.test import TestCase

from uid.models import (
    DictBreed, DictSpecie, DictCountry, DictUberon, DictDevelStage,
    DictPhysioStage)
from common.constants import OBO_URL, GOOD, HIGH

from ..helpers import (
    annotate_breed, annotate_specie, annotate_country, annotate_organismpart,
    annotate_develstage, annotate_physiostage)


class TestAnnotateBreed(TestCase):
    """A class to test annotate breeds"""

    fixtures = [
        "uid/dictbreed",
        "uid/dictcountry",
        "uid/dictspecie"
    ]

    def setUp(self):
        # get a breed object
        self.breed = DictBreed.objects.get(pk=1)

        # erase attributes
        self.breed.mapped_breed = None
        self.breed.mapped_breed_term = None
        self.breed.confidence = None
        self.breed.save()

    @patch("zooma.helpers.use_zooma")
    def test_annotate_breed(self, my_zooma):
        """Testing annotate breed"""

        my_zooma.return_value = {
            'type': 'breed',
            'confidence': 'Good',
            'text': 'Bentheim Black Pied',
            'ontologyTerms': '%s/LBO_0000347' % (OBO_URL)
        }

        # call my method
        annotate_breed(self.breed)

        self.assertTrue(my_zooma.called)

        # ensure annotation
        self.breed.refresh_from_db()

        self.assertEqual(self.breed.mapped_breed, "Bentheim Black Pied")
        self.assertEqual(self.breed.mapped_breed_term, "LBO_0000347")
        self.assertEqual(self.breed.confidence, GOOD)

    @patch("zooma.helpers.use_zooma")
    def test_issue_in_annotate_breed(self, my_zooma):
        """Testing annotate breed with a issue in zooma"""

        my_zooma.side_effect = Exception("Issue with zooma")

        # deal with exception in zooma
        annotate_breed(self.breed)

        self.assertTrue(my_zooma.called)

        # non annotation
        self.breed.refresh_from_db()

        # a non annotated pig has at least the general ontology annotation
        self.assertEqual(self.breed.mapped_breed, "pig breed")
        self.assertEqual(self.breed.mapped_breed_term, "LBO_0000003")
        self.assertIsNone(self.breed.confidence)


class TestAnnotateCountry(TestCase):
    """A class to test annotate countries"""

    fixtures = [
        "uid/dictcountry",
    ]

    def setUp(self):
        # get a country object
        self.country = DictCountry.objects.get(pk=1)

        # erase attributes
        self.country.term = None
        self.country.confidence = None
        self.country.save()

    @patch("zooma.helpers.use_zooma")
    def test_annotate_country(self, my_zooma):
        """Testing annotate country"""

        my_zooma.return_value = {
            'type': 'country',
            'confidence': 'Good',
            'text': 'United Kingdom',
            'ontologyTerms': '%s/NCIT_C17233' % (OBO_URL)}

        # call my method
        annotate_country(self.country)

        self.assertTrue(my_zooma.called)

        # ensure annotation
        self.country.refresh_from_db()

        self.assertEqual(self.country.label, "United Kingdom")
        self.assertEqual(self.country.term, "NCIT_C17233")
        self.assertEqual(self.country.confidence, GOOD)


class TestAnnotateSpecie(TestCase):
    """A class to test annotate species"""

    fixtures = [
        "uid/dictspecie",
    ]

    def setUp(self):
        # get a specie object
        self.specie = DictSpecie.objects.get(pk=1)

        # erase attributes
        self.specie.term = None
        self.specie.confidence = None
        self.specie.save()

    @patch("zooma.helpers.use_zooma")
    def test_annotate_specie(self, my_zooma):
        """Testing annotate specie"""

        my_zooma.return_value = {
            'type': 'specie',
            'confidence': 'Good',
            'text': 'Sus scrofa',
            'ontologyTerms': '%s/NCBITaxon_9823' % (OBO_URL)
        }

        # call my method
        annotate_specie(self.specie)

        self.assertTrue(my_zooma.called)

        # ensure annotation
        self.specie.refresh_from_db()

        self.assertEqual(self.specie.label, "Sus scrofa")
        self.assertEqual(self.specie.term, "NCBITaxon_9823")
        self.assertEqual(self.specie.confidence, GOOD)


class TestAnnotateUberon(TestCase):
    """A class to test annotate uberon"""

    fixtures = [
        "uid/dictuberon",
    ]

    def setUp(self):
        # get a specie object
        self.part = DictUberon.objects.get(pk=1)

        # erase attributes
        self.part.term = None
        self.part.confidence = None
        self.part.save()

    @patch("zooma.helpers.use_zooma")
    def test_annotate_uberon(self, my_zooma):
        """Testing annotate uberon"""

        my_zooma.return_value = {
            'type': 'organism part',
            'confidence': 'Good',
            'text': 'semen',
            'ontologyTerms': '%s/UBERON_0001968' % (OBO_URL)
        }

        # call my method
        annotate_organismpart(self.part)

        self.assertTrue(my_zooma.called)

        # ensure annotation
        self.part.refresh_from_db()

        self.assertEqual(self.part.label, "semen")
        self.assertEqual(self.part.term, "UBERON_0001968")
        self.assertEqual(self.part.confidence, GOOD)


class TestAnnotateDevelStage(TestCase):
    """A class to test developmental stage"""

    fixtures = [
        "uid/dictstage",
    ]

    def setUp(self):
        # get a specie object
        self.stage = DictDevelStage.objects.get(pk=1)

        # erase attributes
        self.stage.term = None
        self.stage.confidence = None
        self.stage.save()

    @patch("zooma.helpers.use_zooma")
    def test_annotate_dictdevelstage(self, my_zooma):
        """Testing annotate dictdevelstage"""

        my_zooma.return_value = {
            'confidence': 'High',
            'ontologyTerms': 'http://www.ebi.ac.uk/efo/EFO_0001272',
            'text': 'adult',
            'type': 'developmental stage'
        }

        # call my method
        annotate_develstage(self.stage)

        self.assertTrue(my_zooma.called)

        # ensure annotation
        self.stage.refresh_from_db()

        self.assertEqual(self.stage.label, "adult")
        self.assertEqual(self.stage.term, "EFO_0001272")
        self.assertEqual(self.stage.confidence, HIGH)


class TestAnnotatePhysioStage(TestCase):
    """A class to test developmental stage"""

    fixtures = [
        "uid/dictstage",
    ]

    def setUp(self):
        # get a specie object
        self.stage = DictPhysioStage.objects.get(pk=1)

        # erase attributes
        self.stage.term = None
        self.stage.confidence = None
        self.stage.save()

    @patch("zooma.helpers.use_zooma")
    def test_annotate_dictphysiostage(self, my_zooma):
        """Testing annotate dictphysiostage"""

        my_zooma.return_value = {
            'confidence': 'High',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/PATO_0001701',
            'text': 'mature',
            'type': 'developmental stage'
        }

        # call my method
        annotate_physiostage(self.stage)

        self.assertTrue(my_zooma.called)

        # ensure annotation
        self.stage.refresh_from_db()

        self.assertEqual(self.stage.label, "mature")
        self.assertEqual(self.stage.term, "PATO_0001701")
        self.assertEqual(self.stage.confidence, HIGH)
