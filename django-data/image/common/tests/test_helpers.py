#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 14:35:36 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import datetime
import json

from django.test import TestCase
from django.utils.dateparse import parse_date
from django.core.validators import validate_email

from .. import constants
from ..helpers import (
    DateDecoder, DateEncoder, format_attribute, get_admin_emails,
    image_timedelta)


class TestImageTimedelta(TestCase):
    """A class to test common.helpers.image_timedelta functions"""

    def test_years(self):
        t1 = parse_date("2019-03-27")
        t2 = parse_date("2018-03-27")

        years, units = image_timedelta(t1, t2)

        self.assertEqual(years, 1)
        self.assertEqual(units, constants.YEARS)

        with self.assertLogs('common.helpers', level="WARNING") as cm:
            # assert date inversion (returns None)
            years, units = image_timedelta(t2, t1)

        self.assertEqual(years, None)
        self.assertEqual(units, constants.YEARS)
        self.assertEqual(len(cm.output), 1)
        self.assertIn("t2>t1", cm.output[0])

    def test_months(self):
        t1 = parse_date("2019-03-27")
        t2 = parse_date("2019-01-27")

        months, units = image_timedelta(t1, t2)

        self.assertEqual(months, 2)
        self.assertEqual(units, constants.MONTHS)

    def test_days(self):
        t1 = parse_date("2019-03-27")
        t2 = parse_date("2019-03-20")

        days, units = image_timedelta(t1, t2)

        self.assertEqual(days, 7)
        self.assertEqual(units, constants.DAYS)

    def test_unknown_date(self):
        t1 = parse_date("2019-03-20")
        t2 = parse_date("1900-01-01")

        with self.assertLogs('common.helpers', level="WARNING") as cm:
            years, units = image_timedelta(t1, t2)

        self.assertIsNone(years)
        self.assertEqual(units, constants.YEARS)
        self.assertEqual(len(cm.output), 1)
        self.assertIn("Ignoring one date", cm.output[0])

    def test_null_date(self):
        t1 = None
        t2 = parse_date("1900-01-01")

        with self.assertLogs('common.helpers', level="WARNING") as cm:
            years, units = image_timedelta(t1, t2)

        self.assertIsNone(years)
        self.assertEqual(units, constants.YEARS)
        self.assertEqual(len(cm.output), 1)
        self.assertIn("One date is NULL", cm.output[0])


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
                "url": "%s/OBI_0100026" % (constants.OBO_URL)
            }]
        }]

        test = format_attribute(
            value="organism",
            terms="OBI_0100026")

        self.assertEqual(reference, test, msg="testing terms")

    def test_null(self):
        test = format_attribute(value=None)

        self.assertIsNone(test)


class TestAdminEmails(TestCase):

    def test_admin_emails(self):
        # calling objects
        emails = get_admin_emails()

        for email in emails:
            self.assertIsNone(validate_email(email))
