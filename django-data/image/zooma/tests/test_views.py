#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 15:59:57 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.tests import GeneralMixinTestCase

from ..views import OntologiesReportView


class OntologiesReportViewTest(GeneralMixinTestCase, TestCase):

    fixtures = [
        "image_app/user",
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
    ]

    def setUp(self):
        """Set up"""

        super().setUp()

        # authenticate
        self.client = Client()
        self.client.login(username='test', password='test')

        # get the url for dashboard
        self.url = reverse('zooma:ontologies_report')

        # get a response
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/zooma/ontologies_report/')
        self.assertIsInstance(view.func.view_class(), OntologiesReportView)
