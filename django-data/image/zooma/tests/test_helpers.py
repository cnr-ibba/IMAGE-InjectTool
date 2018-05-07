#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 16:23:17 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import TestCase

from ..helpers import to_camel_case, from_camel_case, useZooma


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
    def testZooma():
        """Testing zooma tools"""

        # organism in gxa datasource with high, disallow any datasource, good
        # annotation = useZooma('mus musculus','species')

        # country type=null, two matches medium/low, so returned value is None
        # annotation = useZooma('deutschland','country')

        # country type=null, while using ena datasource, high
        # annotation = useZooma('norway','country')

        # breed LBO_0000347    type=null, good
        # annotation = useZooma('bentheim black pied','breed')

        # breed LBO_0000436    type=null, good
        # annotation = useZooma('Bunte Bentheimer','breed')

        # Health status    type=disease
        annotation = useZooma('normal','disease')

        # Organism part
        # annotation = useZooma('spleen','organism part')

        # Organism part UBERON_0001968 (semen) medium for default OLS setting,
        # good for specifying ontologies to search against
        # annotation = useZooma('semen','organism part')

        # Development stage type=developmental stage EFO_0001272 (adult)
        # annotation = useZooma('adult','developmental stage')

        # Physiological stage several medium/low none of them related to
        # physiological stage PATO_0001701 (mature)
        # annotation = useZooma('mature','physiological stage')
        print(annotation)
