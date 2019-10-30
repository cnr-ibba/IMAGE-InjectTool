#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 13:28:23 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase
from django.template import Template, Context

from uid.models import Animal, Sample


class CommonMixin():
    """Does the common stuff when testing cases are run"""

    fixtures = [
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user'
    ]

    def setUp(self):
        self.animal = Animal.objects.get(pk=1)
        self.sample = Sample.objects.get(pk=1)

        self.animal_attributes = [
            'birth_location_accuracy', 'birth_location']
        self.sample_attributes = [
            'collection_place_accuracy', 'collection_place']


class GetAttributeTest(CommonMixin, TestCase):

    TEMPLATE = Template(
        """{% load submissions_filters %}
        {% for show in attributes_to_show %}
            {{ object|getattribute:show }}
        {% endfor %}
        """
    )

    def test_get_attribute_animal(self):
        rendered = self.TEMPLATE.render(
            Context({
                'attributes_to_show': self.animal_attributes,
                'object': self.animal
            }))

        self.assertIn("missing geographic information", rendered)
        self.assertIn("None", rendered)

    def test_get_attribute_sample(self):
        rendered = self.TEMPLATE.render(
            Context({
                'attributes_to_show': self.sample_attributes,
                'object': self.sample
            }))

        self.assertIn("unknown accuracy level", rendered)
        self.assertIn("deutschland", rendered)


class CreateUniqueIDTest(CommonMixin, TestCase):

    TEMPLATE = Template(
        """{% load submissions_filters %}
        {{ object.id|create_unique_id:'to_edit' }}
        """
    )

    def test_create_unique_id(self):
        rendered = self.TEMPLATE.render(
            Context({
                'object': self.animal
            }))

        self.assertIn("to_edit1", rendered)


class ConvertToUmanReadableTest(TestCase):

    TEMPLATE = Template(
        """{% load submissions_filters %}
        {{ attribute_to_edit|convert_to_human_readable:type }}
        """
    )

    def test_convert_to_human_readable_animal(self):
        rendered = self.TEMPLATE.render(
            Context({
                'attribute_to_edit': 'birth_location',
                'type': 'animal'
            }))

        self.assertIn("Birth Location", rendered)

    def test_convert_to_human_readable_sample(self):
        rendered = self.TEMPLATE.render(
            Context({
                'attribute_to_edit': 'collection_place',
                'type': 'sample'
            }))

        self.assertIn("Collection Place", rendered)

    def test_convert_to_human_readable(self):
        rendered = self.TEMPLATE.render(
            Context({
                'attribute_to_edit': 'meow',
                'type': None
            }))

        self.assertIn("meow", rendered)


class ConvertToBiosampleFieldTest(TestCase):

    TEMPLATE = Template(
        """{% load submissions_filters %}
        {{ attribute_to_convert|convert_to_biosample_field }}
        """
    )

    def test_convert_to_biosample_field(self):
        rendered = self.TEMPLATE.render(
            Context({
                'attribute_to_convert': 'Sample storage',
            }))

        self.assertIn("storage", rendered)
