#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 11:14:02 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase
from django.template import Template, Context

from uid.models import Animal


class GetBadgeTest(TestCase):
    """Test get_badges filter function"""

    fixtures = [
        "uid/animal",
        "uid/dictbreed",
        "uid/dictsex",
        "uid/dictspecie",
        "uid/user",
        "uid/dictcountry",
        "uid/dictrole",
        "uid/organization",
        "uid/submission",
        'uid/publication',
        "validation/validationresult"
    ]

    TEMPLATE = Template(
        "{% load validation_tags %}{{ name|get_badge }}"
    )

    def setUp(self):
        # get a name object
        self.animal = Animal.objects.get(pk=1)
        self.validationresult = self.animal.validationresult

    def render(self):
        """Render context"""

        return self.TEMPLATE.render(Context({'name': self.animal}))

    def test_unknown(self):
        """Test an unknown validation"""

        # remove validation object
        self.validationresult.delete()
        self.animal.validationresult = None

        # rdener context
        rendered = self.render()

        self.assertIn('badge-secondary', rendered)
        self.assertIn('>Unknown<', rendered)

    def test_pass(self):
        """Test a passed validation"""

        self.validationresult.status = 'Pass'
        self.validationresult.messages = ["1", "2"]
        self.validationresult.save()

        rendered = self.render()

        self.assertIn('badge-succes', rendered)
        self.assertNotIn('title="', rendered)
        self.assertIn('>Pass<', rendered)

    def test_warning(self):
        """Test a passed validation"""

        self.validationresult.status = 'Warning'
        self.validationresult.messages = ["1", "2"]
        self.validationresult.save()

        rendered = self.render()

        self.assertIn('badge-warning', rendered)
        self.assertIn('title="1<br>2"', rendered)
        self.assertIn('>Warning<', rendered)

    def test_error(self):
        """Test a error validation"""

        self.validationresult.status = 'Error'
        self.validationresult.messages = ["1", "2"]

        rendered = self.render()

        self.assertIn('badge-danger', rendered)
        self.assertIn('title="1<br>2"', rendered)
        self.assertIn('>Error<', rendered)

    def test_info(self):
        """Test a info validation (eg. data need validation"""

        self.validationresult.status = 'Info'
        self.validationresult.messages = ["1", "2"]

        rendered = self.render()

        self.assertIn('badge-info', rendered)
        self.assertIn('title="1<br>2"', rendered)
        self.assertIn('>Info<', rendered)

    def test_default(self):
        """Test default case (not specified) error validation"""

        self.validationresult.status = 'Test Message'
        self.validationresult.messages = ["1", "2"]

        rendered = self.render()

        self.assertIn('badge-danger', rendered)
        self.assertIn('title="1<br>2"', rendered)
        self.assertIn('>Test Message<', rendered)
