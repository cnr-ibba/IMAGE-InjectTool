#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 10:34:44 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import datetime
import json

from django.test import TestCase

from image_app.helper import DateDecoder, DateEncoder


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
