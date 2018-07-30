#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 10:34:44 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import datetime
import json

from django.test import TestCase

from image_app.helpers import DateDecoder, DateEncoder, format_attribute


class JsonTestCase(TestCase):

    def setUp(self):
        """Initialize"""

        # TODO: get a real object
        self.obj = {
                'name': 'Siems_0734_404357',
                'project': 'IMAGE',
                'collectionDate': datetime.date(1991, 7, 26)
                }

        self.json_str = ('{"name": "Siems_0734_404357", "project": "IMAGE", '
                         '"collectionDate": {"text": "1991-07-26", "unit": '
                         '"YYYY-MM-DD"}}')

    def test_encode(self):
        """Encode object as string"""

        json_str = json.dumps(self.obj, cls=DateEncoder)
        self.assertEqual(json_str, self.json_str)

    def test_decode(self):
        """Decode a (image) json string into a obj"""

        obj = json.loads(self.json_str, cls=DateDecoder)
        self.assertEqual(obj, self.obj)

    def test_decode_without_unit(self):
        """Decode a date without unit (returns a string)"""

        obj = {
                'name': 'Siems_0734_404357',
                'project': 'IMAGE',
                'collectionDate': "1991-07-26"
                }

        fake_str = ('{"name": "Siems_0734_404357", "project": "IMAGE", '
                    '"collectionDate": "1991-07-26"}')

        fake_obj = json.loads(fake_str, cls=DateDecoder)
        self.assertEqual(fake_obj, obj)

    def test_encode_a_str_date(self):
        """Encode a string date"""

        fake_obj = {
                'name': 'Siems_0734_404357',
                'project': 'IMAGE',
                'collectionDate': "1991-07-26"
                }

        str_ = ('{"name": "Siems_0734_404357", "project": "IMAGE", '
                '"collectionDate": "1991-07-26"}')

        fake_str = json.dumps(fake_obj, cls=DateEncoder)
        self.assertEqual(fake_str, str_)


class TestAttributes(TestCase):

    def test_format_attribute(self):
        reference = [{
            "value": "54.20944444444445",
            "units": "Decimal degrees"
        }]

        test = format_attribute(
            value="54.20944444444445",
            units="Decimal degrees")

        self.assertEqual(reference, test, msg="testing units")

        # another test
        reference = [{
            "value": "organism",
            "terms": [{
                "url": "http://purl.obolibrary.org/obo/OBI_0100026"
            }]
        }]

        test = format_attribute(
            value="organism",
            terms="OBI_0100026")

        self.assertEqual(reference, test, msg="testing terms")

    def test_null(self):
        test = format_attribute(value=None)

        self.assertIsNone(test)
