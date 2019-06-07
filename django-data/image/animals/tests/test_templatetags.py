#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 16:00:49 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase
from django.template import Template, Context

from image_app.models import Animal

from .common import AnimalFeaturesMixin


class ChildOfTest(AnimalFeaturesMixin, TestCase):
    TEMPLATE = Template(
        "{% load animals_tags %}{{ animal|child_of }}"
    )

    def setUp(self):
        self.animal = Animal.objects.get(pk=3)

    def render(self):
        """render context"""

        return self.TEMPLATE.render(
            Context({'animal': self.animal}))

    def test_no_biosample_ids(self):
        rendered = self.render()
        self.assertEqual(rendered, "IMAGEA000000001, IMAGEA000000002")

    def test_with_biosample_ids(self):
        self.animal.father.biosample_id = "FAKEA123456"
        self.animal.father.save()
        self.animal.mother.biosample_id = "FAKEA123457"
        self.animal.mother.save()

        rendered = self.render()
        self.assertEqual(rendered, "FAKEA123456, FAKEA123457")

    def test_no_father(self):
        self.animal.father = None

        rendered = self.render()
        self.assertEqual(rendered, "IMAGEA000000002")

    def test_no_parents(self):
        self.animal.father = None
        self.animal.mother = None

        rendered = self.render()
        self.assertEqual(rendered, "")
