#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 16:25:51 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from uid.models import (
    DictBreed, DictCountry, DictSpecie, DictUberon, DictDevelStage,
    DictPhysioStage)


class CommandsTestCase(TestCase):
    fixtures = [
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
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

    @patch('zooma.helpers.annotate_organismpart')
    def test_annotate_uberon(self, my_func):
        "Test annotate_organismpart command"

        # mocking objects
        args = []
        opts = {}
        call_command('annotate_organismpart', *args, **opts)

        self.assertTrue(my_func.called)

    @patch('zooma.helpers.annotate_develstage')
    def test_annotate_dictdevelstage(self, my_func):
        "Test annotate_develstage command"

        # mocking objects
        args = []
        opts = {}
        call_command('annotate_develstage', *args, **opts)

        self.assertTrue(my_func.called)

    @patch('zooma.helpers.annotate_physiostage')
    def test_annotate_physiostage(self, my_func):
        "Test annotate_physiostage command"

        # mocking objects
        args = []
        opts = {}
        call_command('annotate_physiostage', *args, **opts)

        self.assertTrue(my_func.called)
