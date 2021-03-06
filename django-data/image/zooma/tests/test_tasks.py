#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 13:34:43 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from unittest.mock import patch, Mock

from django.test import TestCase

from uid.models import (
    DictBreed, DictCountry, DictSpecie, DictUberon, DictDevelStage,
    DictPhysioStage)

from ..tasks import (
    AnnotateBreeds, AnnotateCountries, AnnotateSpecies, AnnotateOrganismPart,
    AnnotateDevelStage, AnnotatePhysioStage, AnnotateAll)


class TestAnnotateBreeds(TestCase):
    """A class to test annotate breeds"""

    fixtures = [
        "uid/dictbreed",
        "uid/dictcountry",
        "uid/dictspecie"
    ]

    def setUp(self):
        self.my_task = AnnotateBreeds()

        # get a breed object
        breed = DictBreed.objects.get(pk=1)

        # erase attributes
        breed.mapped_breed = None
        breed.mapped_breed_term = None
        breed.confidence = None
        breed.save()

    @patch("zooma.tasks.AnnotateBreeds.annotate_func")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)


class TestAnnotateCountries(TestCase):
    """A class to test annotate countries"""

    fixtures = [
        "uid/dictcountry",
    ]

    def setUp(self):
        self.my_task = AnnotateCountries()

        # get a country object
        country = DictCountry.objects.get(pk=1)

        # erase attributes
        country.term = None
        country.confidence = None
        country.save()

    @patch("zooma.tasks.AnnotateCountries.annotate_func")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)


class TestAnnotateSpecies(TestCase):
    """A class to test annotate species"""

    fixtures = [
        "uid/dictspecie",
    ]

    def setUp(self):
        self.my_task = AnnotateSpecies()

        # get a specie object
        specie = DictSpecie.objects.get(pk=1)

        # erase attributes
        specie.term = None
        specie.confidence = None
        specie.save()

    @patch("zooma.tasks.AnnotateSpecies.annotate_func")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)


class TestAnnotateUberon(TestCase):
    """A class to test annotate uberon"""

    fixtures = [
        "uid/dictuberon",
    ]

    def setUp(self):
        self.my_task = AnnotateOrganismPart()

        # get a specie object
        part = DictUberon.objects.get(pk=1)

        # erase attributes
        part.term = None
        part.confidence = None
        part.save()

    @patch("zooma.tasks.AnnotateOrganismPart.annotate_func")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)


class TestAnnotateDictDevelStage(TestCase):
    """A class to test annotate developmental stages"""

    fixtures = [
        "uid/dictstage",
    ]

    def setUp(self):
        self.my_task = AnnotateDevelStage()

        # get a specie object
        stage = DictDevelStage.objects.get(pk=1)

        # erase attributes
        stage.term = None
        stage.confidence = None
        stage.save()

    @patch("zooma.tasks.AnnotateDevelStage.annotate_func")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)


class TestAnnotateDictPhysioStage(TestCase):
    """A class to test annotate physiological stages"""

    fixtures = [
        "uid/dictstage",
    ]

    def setUp(self):
        self.my_task = AnnotatePhysioStage()

        # get a specie object
        stage = DictPhysioStage.objects.get(pk=1)

        # erase attributes
        stage.term = None
        stage.confidence = None
        stage.save()

    @patch("zooma.tasks.AnnotatePhysioStage.annotate_func")
    def test_task(self, my_func):
        res = self.my_task.run()

        # assert a success
        self.assertEqual(res, "success")
        self.assertTrue(my_func.called)


class TestAnnotateAll(TestCase):

    def setUp(self):
        # calling my base setup
        super().setUp()

        # patching objects
        self.mock_group_patcher = patch('zooma.tasks.group')
        self.mock_group = self.mock_group_patcher.start()

        # define a group result object
        result = Mock()
        result.waiting.side_effect = [True, False]
        result.join.return_value = ["success"] * 6
        self.mock_group.return_value.delay.return_value = result

        # define my task
        self.my_task = AnnotateAll()

        # change lock_id (useful when running test during cron)
        self.my_task.lock_id = "test-AnnotateAll"

    def tearDown(self):
        # stopping mock objects
        self.mock_group_patcher.stop()

        # calling base object
        super().tearDown()

    def test_annotateall(self):
        """Test AnnotateAll while a lock is present"""

        res = self.my_task.run()

        # assert success in annotation
        self.assertEqual(res, "success")

        # assert mock objects called
        self.assertTrue(self.mock_group.called)
        self.assertTrue(self.mock_group.return_value.delay.called)

    # Test a non blocking instance
    @patch("redis.lock.Lock.acquire", return_value=False)
    def test_annotateall_nb(self, my_lock):
        """Test AnnotateAll while a lock is present"""

        res = self.my_task.run()

        # assert database is locked
        self.assertEqual(res, "%s already running!" % (self.my_task.name))

        # assert mock objects called
        self.assertFalse(self.mock_group.called)
