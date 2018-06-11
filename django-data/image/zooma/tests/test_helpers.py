#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 16:23:17 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import TestCase

from ..helpers import (
    to_camel_case, from_camel_case, useZooma, get_taxonID_by_scientific_name)


# Create your tests here.
class TestCamelCase(TestCase):
    def test_to_camel_case(self):
        data = [
            "country", "Disease", "Physiological status", "test__string",
            "test _1"
        ]

        reference = [
            'country', 'disease', 'physiologicalStatus', 'testString', 'test1'
        ]

        test = [to_camel_case(el) for el in data]

        self.assertEqual(reference, test)

    def test_from_camel_case(self):
        data = [
            'disease', 'test1', 'country', 'physiologicalStatus', 'testString'
        ]

        reference = [
            'disease', 'test1', 'country', 'physiological status',
            'test string'
        ]

        test = [from_camel_case(el) for el in data]

        self.assertEqual(reference, test)


class TestZooma(TestCase):
    """A class to test zooma tools"""

    def test_use_zooma(self):
        """Testing zooma tools"""

        # HINT: a very slow test. Is it necessary?
        # TODO: enable this test
        return

        # organism in gxa datasource with high, disallow any datasource, good
        reference = {
            'confidence': 'High',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/NCBITaxon_10090',
            'text': 'Mus musculus',
            'type': 'organism'
        }
        test = useZooma('mus musculus', 'species')
        self.assertEqual(
            reference,
            test,
            msg="Testing mus muscolus: species"
        )

        # country type=null, two matches medium/low, so returned value is None
        test = useZooma('deutschland', 'country')
        self.assertIsNone(test, msg="Testing deutschland: country")

        # country type=null, while using ena datasource, high
        # test = useZooma('norway', 'country')
        # self.assertIsNone(test, msg="Testing norway: country")

        # breed LBO_0000347    type=null, good
        reference = {
            'confidence': 'Good',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/LBO_0000347',
            'text': 'Bentheim Black Pied',
            'type': 'breed'
        }
        test = useZooma('bentheim black pied', 'breed')
        self.assertEqual(
            reference,
            test,
            msg="Testing bentheim black pied: breed")

        # breed LBO_0000436    type=null, good
        # annotation = useZooma('Bunte Bentheimer','breed')

        # Health status    type=disease
        reference = {
            'confidence': 'High',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/PATO_0000461',
            'text': 'normal',
            'type': 'disease'
        }
        test = useZooma('normal', 'disease')
        self.assertEqual(
            reference,
            test,
            msg="Testing normal: disease")

        # Organism part
        reference = {
            'confidence': 'High',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/UBERON_0002106',
            'text': 'spleen',
            'type': 'organism part'
        }
        test = useZooma('spleen', 'organism part')
        self.assertEqual(
            reference,
            test,
            msg="Testing spleen: organism part")

        # Organism part UBERON_0001968 (semen) medium for default OLS setting,
        # good for specifying ontologies to search against
        reference = {
            'confidence': 'Good',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/UBERON_0001968',
            'text': 'semen',
            'type': 'organism part'
        }
        test = useZooma('semen', 'organism part')
        self.assertEqual(
            reference,
            test,
            msg="Testing semen: organism part")

        # Development stage type=developmental stage EFO_0001272 (adult)
        reference = {
            'confidence': 'High',
            'ontologyTerms': 'http://www.ebi.ac.uk/efo/EFO_0001272',
            'text': 'adult',
            'type': 'developmental stage'
        }
        test = useZooma('adult', 'developmental stage')
        self.assertEqual(
            reference,
            test,
            msg="Testing adult: developmental stage")

        # Physiological stage several medium/low none of them related to
        # physiological stage PATO_0001701 (mature)
        test = useZooma('mature', 'physiological stage')
        self.assertIsNone(test, msg="Testing mature: physiological stage")


class TestTaxon(TestCase):
    """A class to test taxon services"""

    def test_get_by_scientific_name(self):
        """Testing taxonomy service by scientific name"""

        # HINT: a very slow test. Is it necessary?
        # TODO: enable this test
        return

        # testing a invalid data
        test = get_taxonID_by_scientific_name("foo")
        self.assertIsNone(test)

        # testing a valid name
        test = get_taxonID_by_scientific_name("Homo sapiens")
        self.assertEqual(test, 9606)
