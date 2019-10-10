#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 16:25:51 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from image_app.models import (
    DictBreed, DictCountry, DictSpecie, DictUberon, DictDevelStage,
    DictPhysioStage)


class CommandsTestCase(TestCase):
    fixtures = [
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
    ]

    @classmethod
    def setUpClass(cls):
        """Purging terms from database"""

        super().setUpClass()

        DictBreed.objects.update(term=None)
        DictCountry.objects.update(term=None)
        DictSpecie.objects.update(term=None)
        DictUberon.objects.update(term=None)
        DictDevelStage.objects.update(term=None)
        DictPhysioStage.objects.update(term=None)

    @patch('zooma.helpers.annotate_breed')
    def test_annotate_breeds(self, my_func):
        "Test annotate_breeds command"

        # mocking objects
        args = []
        opts = {}
        call_command('annotate_breeds', *args, **opts)

        self.assertTrue(my_func.called)

    @patch('zooma.helpers.annotate_country')
    def test_annotate_countries(self, my_func):
        "Test annotate_countries command"

        # mocking objects
        args = []
        opts = {}
        call_command('annotate_countries', *args, **opts)

        self.assertTrue(my_func.called)

    @patch('zooma.helpers.annotate_specie')
    def test_annotate_species(self, my_func):
        "Test annotate_species command"

        # mocking objects
        args = []
        opts = {}
        call_command('annotate_species', *args, **opts)

        self.assertTrue(my_func.called)

    @patch('zooma.helpers.annotate_uberon')
    def test_annotate_uberon(self, my_func):
        "Test annotate_uberon command"

        # mocking objects
        args = []
        opts = {}
        call_command('annotate_uberon', *args, **opts)

        self.assertTrue(my_func.called)

    @patch('zooma.helpers.annotate_dictdevelstage')
    def test_annotate_dictdevelstage(self, my_func):
        "Test annotate_dictdevelstage command"

        # mocking objects
        args = []
        opts = {}
        call_command('annotate_dictdevelstage', *args, **opts)

        self.assertTrue(my_func.called)

    @patch('zooma.helpers.annotate_dictphysiostage')
    def test_annotate_dictphysiostage(self, my_func):
        "Test annotate_dictphysiostage command"

        # mocking objects
        args = []
        opts = {}
        call_command('annotate_dictphysiostage', *args, **opts)

        self.assertTrue(my_func.called)