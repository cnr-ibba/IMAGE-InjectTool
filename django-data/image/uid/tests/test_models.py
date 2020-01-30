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
from common.helpers import get_deleted_objects
from common.constants import (
    WAITING, LOADED, ERROR, READY, NEED_REVISION, SUBMITTED, COMPLETED)

from uid.models import (
    Animal, Submission, DictBreed, DictCountry,
    DictSex, DictSpecie, Sample, uid_report, Person, User, db_has_data)

from .mixins import PersonMixinTestCase


class DictSexTestCase(TestCase):
    """Testing DictSex class"""

    fixtures = [
        "uid/dictsex",
        "uid/ontology"
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

    def test_format_attribute_default(self):
        """Testing format attribute with no library_uri"""

        reference = [{
            "value": "male",
            "terms": [{
                "url": "%s/PATO_0000384" % (OBO_URL)
             }]
        }]

        male = DictSex.objects.get(label=self.label)
        male.library_name = None
        test = male.format_attribute()

        self.assertEqual(reference, test)


class DictSpecieTestCase(TestCase):
    """Testing DictSpecie class"""

    fixtures = [
        'uid/dictcountry',
        'uid/dictspecie',
        'uid/ontology',
        'uid/speciesynonym'
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

    def test_missing_taxon(self):
        """test no term returns no taxon"""

        sus = DictSpecie.objects.get(label=self.label)
        sus.term = None
        self.assertIsNone(sus.taxon_id)

    def test_get_specie_by_synonym(self):
        """Getting specie using synonym"""

        sus = DictSpecie.get_by_synonym('Pig', 'United Kingdom')

        self.assertEqual(sus.label, self.label)
        self.assertEqual(sus.term, self.term)

        # assert a specie in a different language (synonym not defined)
        sus = DictSpecie.get_by_synonym('Pig', 'Italy')

        self.assertEqual(sus.label, self.label)
        self.assertEqual(sus.term, self.term)

        # using a word not registered returns no data
        with self.assertRaises(DictSpecie.DoesNotExist):
            DictSpecie.get_by_synonym('Foo', 'United Kingdom')

    def test_get_specie_by_synonym_nospaces(self):
        """Getting specie using synonym, no matters spaces"""

        # assert with spaces
        sus = DictSpecie.get_by_synonym('Pig (domestic)', 'United Kingdom')

        self.assertEqual(sus.label, self.label)
        self.assertEqual(sus.term, self.term)

        # assert without spaces
        sus = DictSpecie.get_by_synonym('Pig(domestic)', 'United Kingdom')

        self.assertEqual(sus.label, self.label)
        self.assertEqual(sus.term, self.term)

    def test_get_specie_check_synonyms(self):
        """Get the same specie from latin or dictionary table"""

        # get a country object
        language = DictCountry.objects.get(label="Italy")

        sus = DictSpecie.get_specie_check_synonyms(
            species_label=self.label,
            language=language)

        self.assertEqual(sus.label, self.label)
        self.assertEqual(sus.term, self.term)

        sus = DictSpecie.get_specie_check_synonyms(
            species_label="Pig",
            language=language)

        self.assertEqual(sus.label, self.label)
        self.assertEqual(sus.term, self.term)


class DictCountryTestCase(TestCase):
    """Testing DictCountry class"""

    fixtures = [
        "uid/dictcountry",
        "uid/ontology"
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
        "uid/dictbreed",
        "uid/dictcountry",
        "uid/dictspecie",
        "uid/ontology"
    ]

    def test_str(self):
        """Testing str representation (as mapped_breed, if present)"""

        breed = DictBreed.objects.get(pk=1)
        self.assertEqual(
            str(breed),
            ("Bunte Bentheimer - United Kingdom (Bentheim Black Pied, "
             "Sus scrofa)"))

        # unset mapped_breed
        breed.mapped_breed = None
        breed.mapped_breed_term = None
        self.assertEqual(
            str(breed),
            "Bunte Bentheimer - United Kingdom (pig breed, Sus scrofa)")

    def test_default_mapped_breed(self):
        """Test mapped breed returns specie.label if no mapping occours"""

        breed = DictBreed.objects.get(pk=1)
        self.assertEqual(breed.mapped_breed, "Bentheim Black Pied")
        self.assertEqual(breed.mapped_breed_term, "LBO_0000347")

        # unset mapped_breed
        breed.mapped_breed = None
        breed.mapped_breed_term = None
        self.assertEqual(breed.mapped_breed, "pig breed")
        self.assertEqual(breed.mapped_breed_term, "LBO_0000003")

    def test_get_no_mapped_breed(self):
        """Test with a specie not defined in get_general_breed_by_species"""

        specie = DictSpecie(label='Anser anser', term="NCBITaxon_8843")
        breed = DictBreed(specie=specie, supplied_breed='Anser anser')

        self.assertIsNone(breed.mapped_breed)
        self.assertIsNone(breed.mapped_breed_term)
        self.assertIsNone(breed.format_attribute())


class SubmissionTestCase(TestCase):
    """Testing Submission class"""

    fixtures = [
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/ontology',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user'
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
        self.assertFalse(self.submission.can_validate())
        self.assertTrue(self.submission.can_submit())

    def test_completed(self):
        """Test completed status"""

        # force submission status
        self.submission.status = COMPLETED

        # test my helper methods
        self.assertTrue(self.submission.can_edit())
        self.assertFalse(self.submission.can_validate())
        self.assertFalse(self.submission.can_submit())

    def test_empty_submission(self):
        """A submission with no data can't be edited"""

        # force submission status to something that can be edited
        self.submission.status = LOADED

        # drop samples
        Sample.objects.all().delete()

        # test my helper methods
        self.assertTrue(self.submission.can_edit())

        # drop also animal.
        Animal.objects.all().delete()

        # now I can't edit a submission
        self.assertFalse(self.submission.can_edit())


class AnimalTestCase(PersonMixinTestCase, TestCase):
    """Testing Animal Class"""

    fixtures = [
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/ontology',
        'uid/organization',
        'uid/publication',
        'uid/submission',
        'uid/user'
    ]

    def setUp(self):
        # create animal
        self.animal = Animal.objects.get(pk=1)
        self.submission = self.animal.submission

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

    def test_to_biosample2(self):
        """testing json conversion with a biosample_id"""

        # assign a different biosample id
        reference = "SAMEA4450079"
        self.animal.biosample_id = reference
        self.animal.save()

        test = self.animal.to_biosample()

        # asserting biosample_.id in response
        self.assertEqual(test["accession"], reference)

    def test_relationship(self):
        """Testing an animal who has mother and father"""

        animal = Animal.objects.get(pk=3)

        test = animal.to_biosample()

        reference = [
            {'alias': 'IMAGEA000000001',
             'relationshipNature': 'child of'},
            {'alias': 'IMAGEA000000002',
             'relationshipNature': 'child of'}
        ]

        # asserting relationship
        self.assertEqual(test['sampleRelationships'], reference)

        # cleaning up relationship (by erasing fk - as crbanim data could be)
        # erase father relationship
        animal.father = None
        animal.save()

        test = animal.to_biosample()

        reference = [
            {'alias': 'IMAGEA000000002',
             'relationshipNature': 'child of'},
        ]

        # asserting relationship
        self.assertEqual(test['sampleRelationships'], reference)

        # cleaning up last relationship
        animal.mother = None
        animal.save()

        test = animal.to_biosample()

        reference = []

        # asserting relationship
        self.assertEqual(test['sampleRelationships'], reference)

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

    fixtures = [
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/ontology',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/submission',
        'uid/user'
    ]

    def setUp(self):
        # create animal
        self.animal = Animal.objects.get(pk=1)

        # now get a sample object
        self.sample = Sample.objects.get(pk=1)

        # set submission
        self.submission = self.sample.submission

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

    def test_to_biosample2(self):
        """testing json conversion with a biosample_id"""

        # assign a different biosample id
        animal_reference = "SAMEA4450079"
        self.animal.biosample_id = animal_reference
        self.animal.save()

        sample_reference = "SAMEA4450075"
        self.sample.biosample_id = sample_reference
        self.sample.save()

        test = self.sample.to_biosample()

        # asserting biosample_.id in response
        self.assertEqual(test["accession"], sample_reference)

        # asserting animal biosample_id in relatioship
        reference = [{
            "accession": animal_reference,
            "relationshipNature": "derived from",
        }]
        self.assertEqual(test['sampleRelationships'], reference)

    def test_to_biosample_no_foreign(self):
        """Testing JSON conversion for biosample submission without
        foreign keys"""

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "biosample_sample.json")
        handle = open(file_path)
        reference = json.load(handle)

        # fix release date to today
        now = timezone.now()
        reference['releaseDate'] = str(now.date())

        # remove foreign keys from reference
        for key in ["Physiological stage", "Developmental stage"]:
            if key in reference["attributes"]:
                del(reference["attributes"][key])

        # remove foreing keys from sample object
        self.sample.physiological_stage = None
        self.sample.developmental_stage = None
        self.sample.save()

        test = self.sample.to_biosample()

        self.maxDiff = None
        self.assertEqual(reference, test)

    # TODO: test biosample with None rendering

    def test_related_object(self):
        """Testing relationship using get_deleted_objects"""

        deletable_objects, model_count, protected = get_deleted_objects(
            [self.animal])

        self.assertEqual(model_count, {'animals': 2, 'samples': 1})

    def test_uid_report(self):
        """testing uid report after a Sample and Animal insert"""

        reference = {
                'n_of_animals': 3,
                'n_of_samples': 1,
                'breeds_total': 1,
                'breeds_without_ontology': 0,
                'countries_total': 3,
                'countries_without_ontology': 0,
                'species_total': 1,
                'species_without_ontology': 0,
                'developmental_stages_total': 1,
                'developmental_stages_without_ontology': 0,
                'organism_parts_total': 1,
                'organism_parts_without_ontology': 0,
                'physiological_stages_total': 1,
                'physiological_stages_without_ontology': 0,
                }

        user = User.objects.get(pk=1)

        test = uid_report(user)

        self.assertEqual(reference, test)

    def test_uid_has_data(self):
        """testing db_has_data for uid"""

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


class PersonTestCase(PersonMixinTestCase, TestCase):
    """Testing Person Class"""

    fixtures = [
        'uid/dictcountry',
        'uid/dictrole',
        'uid/organization',
        'uid/user'
    ]

    def setUp(self):
        # get a person
        self.person = Person.objects.get(user__id=1)

    def test_str(self):
        """test a repr method"""

        test = str(self.person)
        self.assertEqual(
            test, "Foo Bar (Test organization (United Kingdom))")
