#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 16:23:17 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from unittest.mock import patch

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

    def format_response(self, data):
        result = [{
            'annotatedProperty': {
                'propertyType': data['type'],
                'propertyValue': data['text']},
            '_links': {
                'olslinks': [{
                    'semanticTag': data['ontologyTerms']}]
            },
            'confidence': data['confidence'].upper()
        }]

        return result

    @patch('zooma.helpers.requests.get')
    def test_high_confidence(self, mock_get):
        reference = {
            'confidence': 'High',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/NCBITaxon_10090',
            'text': 'Mus musculus',
            'type': 'organism'
        }

        mock_get.return_value.json.return_value = self.format_response(
            reference)

        # organism in gxa datasource with high, disallow any datasource, good
        test = useZooma('mus musculus', 'species')

        self.assertEqual(
            reference,
            test,
            msg="Testing mus muscolus: species"
        )
        self.assertTrue(mock_get.called)

    @patch('zooma.helpers.requests.get')
    def test_medium_confidence(self, mock_get):
        reference = {
            'confidence': 'Medium',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/GAZ_00002646',
            'text': 'Germany',
            'type': 'country'
        }

        mock_get.return_value.json.return_value = self.format_response(
            reference)

        # country type=null, two matches medium/low, so returned value is None
        test = useZooma('deutschland', 'country')

        self.assertIsNone(test, msg="Testing deutschland: country")
        self.assertTrue(mock_get.called)

    @patch('zooma.helpers.requests.get')
    def test_different_type(self, mock_get):
        reference = {
            'confidence': 'Good',
            'ontologyTerms': 'http://www.ebi.ac.uk/efo/EFO_0005290',
            'text': 'Brown Norway',
            'type': 'strain'
        }

        mock_get.return_value.json.return_value = self.format_response(
            reference)

        # country type=null, while using ena datasource, high
        test = useZooma('norway', 'country')

        self.assertIsNone(test, msg="Testing norway: country")
        self.assertTrue(mock_get.called)

    @patch('zooma.helpers.requests.get')
    def test_breed(self, mock_get):
        reference = {
            'confidence': 'Good',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/LBO_0000347',
            'text': 'Bentheim Black Pied',
            'type': 'breed'
        }
        mock_get.return_value.json.return_value = self.format_response(
            reference)

        # breed LBO_0000347    type=null, good
        test = useZooma('bentheim black pied', 'breed')

        self.assertEqual(
            reference,
            test,
            msg="Testing bentheim black pied: breed")
        self.assertTrue(mock_get.called)

    @patch('zooma.helpers.requests.get')
    def test_breed2(self, mock_get):
        reference = {
            'type': 'breed',
            'confidence': 'Good',
            'text': 'Bentheimer Landschaf',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/LBO_0000436'
        }

        mock_get.return_value.json.return_value = self.format_response(
            reference)

        # breed LBO_0000436    type=null, good
        test = useZooma('Bunte Bentheimer', 'breed')

        self.assertEqual(
            reference,
            test,
            msg="Testing bentheim black pied: breed")
        self.assertTrue(mock_get.called)

    @patch('zooma.helpers.requests.get')
    def test_disease(self, mock_get):

        reference = {
            'confidence': 'High',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/PATO_0000461',
            'text': 'normal',
            'type': 'disease'
        }

        mock_get.return_value.json.return_value = self.format_response(
            reference)

        # Health status    type=disease
        test = useZooma('normal', 'disease')

        self.assertEqual(
            reference,
            test,
            msg="Testing normal: disease")
        self.assertTrue(mock_get.called)

    @patch('zooma.helpers.requests.get')
    def test_organism_part(self, mock_get):
        reference = {
            'confidence': 'High',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/UBERON_0002106',
            'text': 'spleen',
            'type': 'organism part'
        }

        mock_get.return_value.json.return_value = self.format_response(
            reference)

        # Organism part
        test = useZooma('spleen', 'organism part')

        self.assertEqual(
            reference,
            test,
            msg="Testing spleen: organism part")
        self.assertTrue(mock_get.called)

    @patch('zooma.helpers.requests.get')
    def test_organism_part2(self, mock_get):
        reference = {
            'confidence': 'Good',
            'ontologyTerms': 'http://purl.obolibrary.org/obo/UBERON_0001968',
            'text': 'semen',
            'type': 'organism part'
        }

        mock_get.return_value.json.return_value = self.format_response(
            reference)

        # Organism part UBERON_0001968 (semen) medium for default OLS setting,
        # good for specifying ontologies to search against
        test = useZooma('semen', 'organism part')

        self.assertEqual(
            reference,
            test,
            msg="Testing semen: organism part")
        self.assertTrue(mock_get.called)

    @patch('zooma.helpers.requests.get')
    def test_stage(self, mock_get):
        reference = {
            'confidence': 'High',
            'ontologyTerms': 'http://www.ebi.ac.uk/efo/EFO_0001272',
            'text': 'adult',
            'type': 'developmental stage'
        }

        mock_get.return_value.json.return_value = self.format_response(
            reference)

        # Development stage type=developmental stage EFO_0001272 (adult)
        test = useZooma('adult', 'developmental stage')

        self.assertEqual(
            reference,
            test,
            msg="Testing adult: developmental stage")
        self.assertTrue(mock_get.called)


class TestTaxon(TestCase):
    """A class to test taxon services"""

    def test_get_by_scientific_name(self):
        """Testing taxonomy service by scientific name"""

        # testing a invalid data
        with patch('zooma.helpers.requests.get') as mock_get:
            mock_get.return_value.status_code = 404
            mock_get.return_value.text = 'No results.'

            test = get_taxonID_by_scientific_name("foo")
            self.assertIsNone(test)
            self.assertTrue(mock_get.called)

        # testing a valid name
        with patch('zooma.helpers.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = [{'taxId': '9606'}]

            # testing functions
            test = get_taxonID_by_scientific_name("Homo sapiens")
            self.assertEqual(test, 9606)
            self.assertTrue(mock_get.called)
