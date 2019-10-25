#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:24:03 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import json

from unittest.mock import patch

from pyUSIrest.auth import Auth

from django.test import TestCase
from django.template import Template, Context

from common.constants import BIOSAMPLE_URL

from .common import generate_token


class GetBiosampleLink(TestCase):
    TEMPLATE = Template(
        "{% load biosample_tags %}{{ biosample_id|get_biosample_link }}"
    )

    def test_unknown(self):
        """Test a None biosample id"""

        rendered = self.TEMPLATE.render(Context({'biosample_id': None}))

        self.assertIn('None', rendered)

    def test_biosample_id(self):
        """Test a Fake biosample id"""

        rendered = self.TEMPLATE.render(
            Context({'biosample_id': "FAKEA0123456"}))

        self.assertIn(
            '%s/FAKEA0123456' % (BIOSAMPLE_URL),
            rendered)


class ToJsonTestCase(TestCase):
    TEMPLATE = Template(
        "{% load json_tags %}{{ auth.claims|to_json }}"
    )

    def test_render_token(self):
        """test token rendering with to_json template tags"""

        rendered = self.TEMPLATE.render(
            Context({'auth': Auth(token=generate_token())}))

        self.assertIsInstance(rendered, str)

        data = json.loads(rendered)
        self.assertIsInstance(data, dict)


class IsBiosampleTestEnv(TestCase):
    TEMPLATE = Template(
        "{% load biosample_tags %}{% is_biosample_test_env %}"
    )

    @patch("biosample.templatetags.biosample_tags.BIOSAMPLE_URL",
           "https://wwwdev.ebi.ac.uk/biosamples/samples")
    @patch("biosample.templatetags.biosample_tags.EBI_AAP_API_AUTH",
           "https://explore.api.aai.ebi.ac.uk/auth")
    @patch("biosample.templatetags.biosample_tags.BIOSAMPLE_API_ROOT",
           "https://submission-test.ebi.ac.uk/api/")
    def test_is_biosample_test_env(self):
        rendered = self.TEMPLATE.render(Context({}))
        self.assertIn("True", rendered)

    @patch("biosample.templatetags.biosample_tags.BIOSAMPLE_URL",
           "https://www.ebi.ac.uk/biosamples/samples")
    @patch("biosample.templatetags.biosample_tags.EBI_AAP_API_AUTH",
           "https://api.aai.ebi.ac.uk/auth")
    @patch("biosample.templatetags.biosample_tags.BIOSAMPLE_API_ROOT",
           "https://submission.ebi.ac.uk/api/")
    def test_is_not_biosample_test_env(self):
        rendered = self.TEMPLATE.render(Context({}))
        self.assertIn("False", rendered)
