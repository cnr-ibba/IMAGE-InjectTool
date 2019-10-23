#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:24:03 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase
from django.template import Template, Context

from common.constants import BIOSAMPLE_URL


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
