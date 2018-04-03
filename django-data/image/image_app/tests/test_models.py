#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 12:16:55 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import TestCase

from image_app.models import DictBreed, DictSex


class DictSexTestCase(TestCase):
    """Testing DictSex class"""

    def setUp(self):
        DictSex.objects.create(
                label='male', short_form='PATO_0000384')

    def test_to_biosample(self):
        """Testing sex to biosample json"""

        reference = {
            "text": "male",
            "ontologyTerms": "PATO_0000384"
        }

        male = DictSex.objects.get(label="male")
        test = male.to_biosample()

        self.assertEqual(reference, test)


class DictBreedTestCase(TestCase):
    """Testing DictBreed class"""

    def setUp(self):
        DictBreed.objects.create(
                supplied_breed='Bunte Bentheimer',
                mapped_breed='Bentheim Black Pied',
                mapped_breed_ontology_accession='LBO_0000347',
                country='Germany',
                country_ontology_accession='NCIT_C16636',
                species='Sus scrofa',
                species_ontology_accession='NCBITaxon_9823')

    def test_to_biosample(self):
        """Testing breed to biosample json"""

        reference = {
            "suppliedBreed": "Bunte Bentheimer",
            "country": {
                "text": "Germany",
                "ontologyTerms": "NCIT_C16636"
            },
            "mappedBreed": {
                "text": "Bentheim Black Pied",
                "ontologyTerms": "LBO_0000347"
            }
        }

        bunte = DictBreed.objects.get(supplied_breed='Bunte Bentheimer')
        test = bunte.to_biosample()

        self.assertEqual(reference, test)
