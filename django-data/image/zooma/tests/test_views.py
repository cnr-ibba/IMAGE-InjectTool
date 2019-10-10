#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 15:59:57 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import resolve, reverse

from common.tests import GeneralMixinTestCase

from ..views import (
    OntologiesReportView, AnnotateBreedsView, AnnotateCountriesView,
    AnnotateSpeciesView, AnnotateOrganismPartView, AnnotateDevelStageView,
    AnnotatePhysioStageView)


class OntologiesMixin():
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


class OntologiesReportViewTest(
        OntologiesMixin, GeneralMixinTestCase, TestCase):

    def setUp(self):
        """Set up"""

        super().setUp()

        # get the url for dashboard
        self.url = reverse('zooma:ontologies_report')

        # get a response
        self.response = self.client.get(self.url)

    def test_url_resolves_view(self):
        view = resolve('/zooma/ontologies_report/')
        self.assertIsInstance(view.func.view_class(), OntologiesReportView)


class AnnotateViewMixinTest(OntologiesMixin, GeneralMixinTestCase):

    task_name = "AnnotateBreeds"
    zooma_url = "annotate_breeds"
    view_class = AnnotateBreedsView

    def setUp(self):
        """Set up"""

        super().setUp()

        # get the url for dashboard
        self.url = reverse('zooma:%s' % self.zooma_url)

        # get a response with an ajax request
        self.response = self.client.get(
            self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_url_resolves_view(self):
        view = resolve('/zooma/%s/' % (self.zooma_url))
        self.assertIsInstance(view.func.view_class(), self.view_class)

    def test_non_ajax_call(self):
        """A non ajax call reply 400 status"""

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

    def test_post_start_task(self, my_task):
        response = self.client.post(
            self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {'status': '%s started' % (self.task_name)})
        self.assertTrue(my_task.called)


class AnnotateBreedViewTest(AnnotateViewMixinTest, TestCase):

    task_name = "AnnotateBreeds"
    zooma_url = "annotate_breeds"
    view_class = AnnotateBreedsView

    @patch("zooma.tasks.AnnotateBreeds.delay")
    def test_post_start_task(self, my_task):
        super().test_post_start_task(my_task)


class AnnotateCountriesViewTest(AnnotateViewMixinTest, TestCase):

    task_name = "AnnotateCountries"
    zooma_url = "annotate_countries"
    view_class = AnnotateCountriesView

    @patch("zooma.tasks.AnnotateCountries.delay")
    def test_post_start_task(self, my_task):
        super().test_post_start_task(my_task)


class AnnotateSpeciesViewTest(AnnotateViewMixinTest, TestCase):

    task_name = "AnnotateSpecies"
    zooma_url = "annotate_species"
    view_class = AnnotateSpeciesView

    @patch("zooma.tasks.AnnotateSpecies.delay")
    def test_post_start_task(self, my_task):
        super().test_post_start_task(my_task)


class AnnotateOrganismPartViewTest(AnnotateViewMixinTest, TestCase):

    task_name = "AnnotateOrganismPart"
    zooma_url = "annotate_organismparts"
    view_class = AnnotateOrganismPartView

    @patch("zooma.tasks.AnnotateOrganismPart.delay")
    def test_post_start_task(self, my_task):
        super().test_post_start_task(my_task)


class AnnotateDevelStageViewTest(AnnotateViewMixinTest, TestCase):

    task_name = "AnnotateDevelStage"
    zooma_url = "annotate_develstages"
    view_class = AnnotateDevelStageView

    @patch("zooma.tasks.AnnotateDevelStage.delay")
    def test_post_start_task(self, my_task):
        super().test_post_start_task(my_task)


class AnnotatePhysioStageViewTest(AnnotateViewMixinTest, TestCase):

    task_name = "AnnotatePhysioStage"
    zooma_url = "annotate_physiostages"
    view_class = AnnotatePhysioStageView

    @patch("zooma.tasks.AnnotatePhysioStage.delay")
    def test_post_start_task(self, my_task):
        super().test_post_start_task(my_task)
