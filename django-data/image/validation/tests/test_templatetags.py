#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 11:14:02 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import Mock

from django.test import TestCase
from django.template import Template, Context

from image_app.models import Name


class GetBadgeTest(TestCase):
    """Test get_badges filter function"""

    TEMPLATE = Template(
        "{% load validation_tags %}{{ name|get_badge }}"
    )

    def test_unknown(self):
        """Test an unknown validation"""

        name = Name()

        rendered = self.TEMPLATE.render(
            Context({'name': name}))

        self.assertIn('badge-secondary', rendered)
        self.assertIn('>Unknown<', rendered)

    def test_pass(self):
        """Test a passed validation"""

        name = Mock()
        name.validationresult.status = 'Pass'
        name.validationresult.result.get_messages.return_value = ["1", "2"]

        rendered = self.TEMPLATE.render(
            Context({'name': name}))

        self.assertIn('badge-succes', rendered)
        self.assertNotIn('title="', rendered)
        self.assertIn('>Pass<', rendered)

    def test_warning(self):
        """Test a passed validation"""

        name = Mock()
        name.validationresult.status = 'Warning'
        name.validationresult.result.get_messages.return_value = ["1", "2"]

        rendered = self.TEMPLATE.render(
            Context({'name': name}))

        self.assertIn('badge-warning', rendered)
        self.assertIn('title="1<br>2"', rendered)
        self.assertIn('>Warning<', rendered)

    def test_error(self):
        """Test a error validation"""

        name = Mock()
        name.validationresult.status = 'Error'
        name.validationresult.result.get_messages.return_value = ["1", "2"]

        rendered = self.TEMPLATE.render(
            Context({'name': name}))

        self.assertIn('badge-danger', rendered)
        self.assertIn('title="1<br>2"', rendered)
        self.assertIn('>Error<', rendered)

    def test_default(self):
        """Test a error validation"""

        name = Mock()
        name.validationresult.status = 'Test Message'
        name.validationresult.result.get_messages.return_value = ["1", "2"]

        rendered = self.TEMPLATE.render(
            Context({'name': name}))

        self.assertIn('badge-danger', rendered)
        self.assertIn('title="1<br>2"', rendered)
        self.assertIn('>Test Message<', rendered)
