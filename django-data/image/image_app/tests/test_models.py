#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 12:16:55 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import os
import json

from django.test import TestCase
from django.utils import timezone

from common.constants import OBO_URL
from common.tests import PersonMixinTestCase
from common.constants import (
    WAITING, LOADED, ERROR, READY, NEED_REVISION, SUBMITTED, COMPLETED)

from image_app.models import (Animal, Submission, DictBreed, DictCountry,
                              DictSex, DictSpecie, Sample, uid_report,
                              Person, User, db_has_data)


class DictSexTestCase(TestCase):
    """Testing DictSex class"""

    fixtures = [
        "image_app/dictsex",
        "image_app/ontology"
    ]

    def setUp(self):
        # my attributes
        self.label = 'male'
        self.term = 'PATO_0000384'

    def test_str(self):
        """Testing str representation"""

        male = DictSex.objects.get(label=self.label)
        self.assertEqual(
                str(male),
                "{label} ({term})".format(
                        label=self.label,
                        term=self.term))

    def test_format_attribute(self):
        """Testing format attribute"""

        reference = [{
            "value": "male",
            "terms": [{
                "url": "%s/PATO_0000384" % (OBO_URL)
             }]
        }]

        male = DictSex.objects.get(label=self.label)
        test = male.format_attribute()

        self.assertEqual(reference, test)


class DictSpecieTestCase(TestCase):
    """Testing DictSpecie class"""

    fixtures = [
        'image_app/dictcountry',
        'image_app/dictspecie',
        'image_app/ontology',
        'image_app/speciesynonim'
    ]

    def setUp(self):
        # my attributes
        self.label = 'Sus scrofa'
        self.term = 'NCBITaxon_9823'

    def test_str(self):
        """Testing str representation"""

        sus = DictSpecie.objects.get(label=self.label)
        self.assertEqual(
                str(sus),
                "{label} ({term})".format(
                        label=self.label,
                        term=self.term))

    def test_get_specie_by_synonim(self):
        """Getting specie using synonim"""

        sus = DictSpecie.get_by_synonim('Pig', 'United Kingdom')

        self.assertEqual(sus.label, self.label)
        self.assertEqual(sus.term, self.term)

        # assert a specie in a different language (synonim not defined)
        sus = DictSpecie.get_by_synonim('Pig', 'Italy')

        self.assertEqual(sus.label, self.label)
        self.assertEqual(sus.term, self.term)

        # using a word not registered returns no data
        with self.assertRaises(DictSpecie.DoesNotExist):
            DictSpecie.get_by_synonim('Foo', 'United Kingdom')


class DictCountryTestCase(TestCase):
    """Testing DictCountry class"""

    fixtures = [
        "image_app/dictcountry",
        "image_app/ontology"
    ]

    def setUp(self):
        # my attributes
        self.label = 'United Kingdom'
        self.term = 'NCIT_C17233'

    def test_str(self):
        """Testing str representation"""

        uk = DictCountry.objects.get(label=self.label)
        self.assertEqual(
                str(uk),
                "{label} ({term})".format(
                        label=self.label,
                        term=self.term))


class DictBreedTestCase(TestCase):
    """Testing DictBreed class"""

    fixtures = [
        "image_app/dictbreed",
        "image_app/dictcountry",
        "image_app/dictspecie",
        "image_app/ontology"
    ]

    def test_str(self):
        """Testing str representation (as mapped_breed, if present)"""

        breed = DictBreed.objects.get(pk=1)
        self.assertEqual(
            str(breed),
            "Bunte Bentheimer (Bentheim Black Pied, Sus scrofa)")

        # unset mapped_breed
        breed.mapped_breed = None
        self.assertEqual(
            str(breed), "Bunte Bentheimer (None, Sus scrofa)")


class SubmissionTestCase(TestCase):
    """Testing Submission class"""

    fixtures = [
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/ontology',
        'image_app/organization',
        'image_app/submission',
        'image_app/user'
    ]

    def setUp(self):
        self.submission = Submission.objects.get(pk=1)

    def test_str(self):
        test = str(self.submission)
        reference = "Cryoweb (United Kingdom, test)"

        self.assertEqual(reference, test)

    def test_waiting(self):
        """Test waiting status"""

        # force submission status
        self.submission.status = WAITING

        # test my helper methods
        self.assertFalse(self.submission.can_edit())
        self.assertFalse(self.submission.can_validate())
        self.assertFalse(self.submission.can_submit())

    def test_loaded(self):
        """Test loaded status"""

        # force submission status
        self.submission.status = LOADED

        # test my helper methods
        self.assertTrue(self.submission.can_edit())
        self.assertTrue(self.submission.can_validate())
        self.assertFalse(self.submission.can_submit())

    def test_submitted(self):
        """Test submitted status"""

        # force submission status
        self.submission.status = SUBMITTED

        # test my helper methods
        self.assertFalse(self.submission.can_edit())
        self.assertFalse(self.submission.can_validate())
        self.assertFalse(self.submission.can_submit())

    def test_error(self):
        """Test error status"""

        # force submission status
        self.submission.status = ERROR

        # test my helper methods
        self.assertTrue(self.submission.can_edit())
        self.assertFalse(self.submission.can_validate())
        self.assertFalse(self.submission.can_submit())

    def test_need_revision(self):
        """Test need_revision status"""

        # force submission status
        self.submission.status = NEED_REVISION

        # test my helper methods
        self.assertTrue(self.submission.can_edit())
        self.assertTrue(self.submission.can_validate())
        self.assertFalse(self.submission.can_submit())

    def test_ready(self):
        """Test ready status"""

        # force submission status
        self.submission.status = READY

        # test my helper methods
        self.assertTrue(self.submission.can_edit())
        self.assertTrue(self.submission.can_validate())
        self.assertTrue(self.submission.can_submit())

    def test_completed(self):
        """Test completed status"""

        # force submission status
        self.submission.status = COMPLETED

        # test my helper methods
        self.assertTrue(self.submission.can_edit())
        self.assertFalse(self.submission.can_validate())
        self.assertFalse(self.submission.can_submit())


class AnimalTestCase(PersonMixinTestCase, TestCase):
    """Testing Animal Class"""

    # an attribute for PersonMixinTestCase
    person = Person

    fixtures = [
        'image_app/animal',
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/name',
        'image_app/ontology',
        'image_app/organization',
        'image_app/publication',
        'image_app/submission',
        'image_app/user'
    ]

    def setUp(self):
        # create animal
        self.animal = Animal.objects.get(pk=1)
        self.submission = self.animal.submission

    def test_get_biosample_id(self):
        """Get a biosample id or a temporary id"""

        reference = "animal_%s" % (self.animal.id)

        test = self.animal.get_biosample_id()
        self.assertEqual(reference, test)

        # assign a different biosample id
        reference = "SAMEA4450079"
        self.animal.name.biosample_id = reference
        self.animal.save()

        test = self.animal.get_biosample_id()
        self.assertEqual(reference, test)

    def test_to_biosample(self):
        """Testing JSON conversion for biosample submission"""

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "biosample_animal.json")
        handle = open(file_path)
        reference = json.load(handle)

        # fix release date to today
        now = timezone.now()
        reference['releaseDate'] = str(now.date())

        test = self.animal.to_biosample()

        self.maxDiff = None
        self.assertEqual(reference, test)

    # TODO: test None rendering

    def test_waiting(self):
        """Test waiting status"""

        # force submission status
        self.submission.status = WAITING
        self.submission.save()

        # test my helper methods
        self.assertFalse(self.animal.can_delete())
        self.assertFalse(self.animal.can_edit())

    def test_loaded(self):
        """Test loaded status"""

        # force submission status
        self.submission.status = LOADED
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.animal.can_delete())
        self.assertTrue(self.animal.can_edit())

    def test_submitted(self):
        """Test submitted status"""

        # force submission status
        self.submission.status = SUBMITTED
        self.submission.save()

        # test my helper methods
        self.assertFalse(self.animal.can_delete())
        self.assertFalse(self.animal.can_edit())

    def test_error(self):
        """Test error status"""

        # force submission status
        self.submission.status = ERROR
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.animal.can_delete())
        self.assertTrue(self.animal.can_edit())

    def test_need_revision(self):
        """Test need_revision status"""

        # force submission status
        self.submission.status = NEED_REVISION
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.animal.can_delete())
        self.assertTrue(self.animal.can_edit())

    def test_ready(self):
        """Test ready status"""

        # force submission status
        self.submission.status = READY
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.animal.can_delete())
        self.assertTrue(self.animal.can_edit())

    def test_completed(self):
        """Test completed status"""

        # force submission status
        self.submission.status = COMPLETED
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.animal.can_delete())
        self.assertTrue(self.animal.can_edit())


class SampleTestCase(PersonMixinTestCase, TestCase):
    """testing sample class"""

    # an attribute for PersonMixinTestCase
    person = Person

    fixtures = [
        'image_app/animal',
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
        'image_app/name',
        'image_app/ontology',
        'image_app/organization',
        'image_app/publication',
        'image_app/sample',
        'image_app/submission',
        'image_app/user'
    ]

    def setUp(self):
        # create animal
        self.animal = Animal.objects.get(pk=1)

        # now get a sample object
        self.sample = Sample.objects.get(pk=1)

        # set submission
        self.submission = self.sample.submission

    def test_get_biosample_id(self):
        """Get a biosample id or a temporary id"""

        reference = "sample_%s" % (self.sample.id)

        test = self.sample.get_biosample_id()
        self.assertEqual(reference, test)

        # assign a different biosample id
        reference = "SAMEA4450075"
        self.sample.name.biosample_id = reference
        self.sample.save()

        test = self.sample.get_biosample_id()
        self.assertEqual(reference, test)

    def test_to_biosample(self):
        """Testing JSON conversion for biosample submission"""

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "biosample_sample.json")
        handle = open(file_path)
        reference = json.load(handle)

        # fix release date to today
        now = timezone.now()
        reference['releaseDate'] = str(now.date())

        test = self.sample.to_biosample()

        self.maxDiff = None
        self.assertEqual(reference, test)

    # TODO: test biosample with None rendering

    def test_uid_report(self):
        """testing uid report after a Sample and Animal insert"""

        reference = {
                'n_of_animals': 1,
                'n_of_samples': 1,
                'breeds_without_ontology': 0,
                'countries_without_ontology': 0,
                'species_without_ontology': 0,
                }

        user = User.objects.get(pk=1)

        test = uid_report(user)

        self.assertEqual(reference, test)

    def test_uid_has_data(self):
        """testing db_has_data for image_app"""

        self.assertTrue(db_has_data())

    def test_waiting(self):
        """Test waiting status"""

        # force submission status
        self.submission.status = WAITING
        self.submission.save()

        # test my helper methods
        self.assertFalse(self.sample.can_delete())
        self.assertFalse(self.sample.can_edit())

    def test_loaded(self):
        """Test loaded status"""

        # force submission status
        self.submission.status = LOADED
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.sample.can_delete())
        self.assertTrue(self.sample.can_edit())

    def test_submitted(self):
        """Test submitted status"""

        # force submission status
        self.submission.status = SUBMITTED
        self.submission.save()

        # test my helper methods
        self.assertFalse(self.sample.can_delete())
        self.assertFalse(self.sample.can_edit())

    def test_error(self):
        """Test error status"""

        # force submission status
        self.submission.status = ERROR
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.sample.can_delete())
        self.assertTrue(self.sample.can_edit())

    def test_need_revision(self):
        """Test need_revision status"""

        # force submission status
        self.submission.status = NEED_REVISION
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.sample.can_delete())
        self.assertTrue(self.sample.can_edit())

    def test_ready(self):
        """Test ready status"""

        # force submission status
        self.submission.status = READY
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.sample.can_delete())
        self.assertTrue(self.sample.can_edit())

    def test_completed(self):
        """Test completed status"""

        # force submission status
        self.submission.status = COMPLETED
        self.submission.save()

        # test my helper methods
        self.assertTrue(self.sample.can_delete())
        self.assertTrue(self.sample.can_edit())
