#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 16:23:17 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from unittest.mock import patch

from django.test import TestCase

from image_app.models import DictBreed, DictSpecie, DictCountry, CONFIDENCES
from common.constants import OBO_URL

from ..helpers import (
    to_camel_case, from_camel_case, useZooma, get_taxonID_by_scientific_name,
    annotate_breed, annotate_specie, annotate_country)

# some statuses. Confidence could be a inherithed object
GOOD = CONFIDENCES.get_value('good')


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
            'ontologyTerms': '%s/NCBITaxon_10090' % (OBO_URL),
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
            'ontologyTerms': '%s/GAZ_00002641' % (OBO_URL),
            'text': 'England',
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
            'ontologyTerms': '%s/LBO_0000347' % (OBO_URL),
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
            'ontologyTerms': '%s/LBO_0000436' % (OBO_URL)
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
            'ontologyTerms': '%s/PATO_0000461' % (OBO_URL),
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
            'ontologyTerms': '%s/UBERON_0002106' % (OBO_URL),
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
            'ontologyTerms': '%s/UBERON_0001968' % (OBO_URL),
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


class TestAnnotateBreed(TestCase):
    """A class to test annotate breeds"""

    fixtures = [
        "image_app/dictbreed",
        "image_app/dictcountry",
        "image_app/dictspecie"
    ]

    def setUp(self):
        # get a breed object
        self.breed = DictBreed.objects.get(pk=1)

        # erase attributes
        self.breed.mapped_breed = None
        self.breed.mapped_breed_term = None
        self.breed.confidence = None
        self.breed.save()

    @patch("zooma.helpers.useZooma")
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

    @patch("zooma.helpers.useZooma")
    def test_no_annotation(self, my_zooma):
        """Ignore terms with non expected ontology"""

        # a fake object
        my_zooma.return_value = {
            'type': 'breed',
            'confidence': 'Good',
            'text': 'Bentheim Black Pied',
            'ontologyTerms': '%s/GAZ_00002641' % (OBO_URL)
        }

        # call my method
        annotate_breed(self.breed)

        self.assertTrue(my_zooma.called)

        # ensure annotation
        self.breed.refresh_from_db()

        self.assertIsNone(self.breed.mapped_breed)
        self.assertIsNone(self.breed.mapped_breed_term)
        self.assertIsNone(self.breed.confidence)


class TestAnnotateCountry(TestCase):
    """A class to test annotate countries"""

    fixtures = [
        "image_app/dictcountry",
    ]

    def setUp(self):
        # get a country object
        self.country = DictCountry.objects.get(pk=1)

        # erase attributes
        self.country.term = None
        self.country.confidence = None
        self.country.save()

    @patch("zooma.helpers.useZooma")
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

    @patch("zooma.helpers.useZooma")
    def test_no_annotation(self, my_zooma):
        """Ignore terms with non expected ontology"""

        # a fake object
        my_zooma.return_value = {
            'type': 'country',
            'confidence': 'Good',
            'text': 'England',
            'ontologyTerms': '%s/LBO_0000347' % (OBO_URL)
        }

        # call my method
        annotate_country(self.country)

        self.assertTrue(my_zooma.called)

        # ensure annotation
        self.country.refresh_from_db()

        self.assertIsNone(self.country.term)
        self.assertIsNone(self.country.confidence)


class TestAnnotateSpecie(TestCase):
    """A class to test annotate species"""

    fixtures = [
        "image_app/dictspecie",
    ]

    def setUp(self):
        # get a specie object
        self.specie = DictSpecie.objects.get(pk=1)

        # erase attributes
        self.specie.term = None
        self.specie.confidence = None
        self.specie.save()

    @patch("zooma.helpers.useZooma")
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

    @patch("zooma.helpers.useZooma")
    def test_no_annotation(self, my_zooma):
        """Ignore terms with non expected ontology"""

        # a fake object
        my_zooma.return_value = {
            'type': 'specie',
            'confidence': 'Good',
            'text': 'England',
            'ontologyTerms': '%s/LBO_0000347' % (OBO_URL)
        }

        # call my method
        annotate_specie(self.specie)

        self.assertTrue(my_zooma.called)

        # ensure annotation
        self.specie.refresh_from_db()

        self.assertIsNone(self.specie.term)
        self.assertIsNone(self.specie.confidence)
