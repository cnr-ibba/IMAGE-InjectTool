#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 12:16:55 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import os
import json
import datetime

from django.test import TestCase

from image_app.models import (Animal, Submission, DictBreed, DictCountry,
                              DictSex, DictSpecie, Sample, uid_report,
                              Person)

from validation.helpers.biosample import AnimalValidator, SampleValidator

from ..constants import OBO_URL


class DictSexTestCase(TestCase):
    """Testing DictSex class"""

    fixtures = ["image_app/dictsex"]

    def setUp(self):
        # my attributes
        self.label = 'male'
        self.term = 'PATO_0000384'

    def test_to_validation(self):
        """Testing sex to biosample json"""

        reference = {
            "text": self.label,
            "ontologyTerms": "/".join([
                OBO_URL,
                self.term]
            ),
        }

        male = DictSex.objects.get(label=self.label)
        test = male.to_validation()

        self.assertEqual(reference, test)

    def test_to_validation_with_none(self):
        """Test to biosample conversion without term"""

        male = DictSex.objects.get(label=self.label)
        male.term = None
        test = male.to_validation()

        reference = {
            "text": self.label
        }

        self.assertEqual(reference, test)

    def test_str(self):
        """Testing str representation"""

        male = DictSex.objects.get(label=self.label)
        self.assertEqual(
                str(male),
                "{label} ({term})".format(
                        label=self.label,
                        term=self.term))


class DictSpecieTestCase(TestCase):
    """Testing DictSpecie class"""

    fixtures = [
        "image_app/dictspecie",
        "image_app/dictcountry",
        "image_app/speciesynonim"]

    def setUp(self):
        # my attributes
        self.label = 'Sus scrofa'
        self.term = 'NCBITaxon_9823'

    def test_to_validation(self):
        """Testing specie to biosample json"""

        reference = {
            "text": self.label,
            "ontologyTerms": "/".join([
                OBO_URL,
                self.term]
            ),
        }

        print(DictSpecie.objects.all())

        sus = DictSpecie.objects.get(label=self.label)
        test = sus.to_validation()

        self.assertEqual(reference, test)

    def test_to_validation_with_none(self):
        """Test to biosample conversion without term"""

        sus = DictSpecie.objects.get(label=self.label)
        sus.term = None
        test = sus.to_validation()

        reference = {
            "text": self.label
        }

        self.assertEqual(reference, test)

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

        sus = DictSpecie.get_by_synonim('Pig', 'Germany')

        self.assertEqual(sus.label, self.label)
        self.assertEqual(sus.term, self.term)

        # using a word not registered returns no data
        with self.assertRaises(DictSpecie.DoesNotExist):
            DictSpecie.get_by_synonim('Foo', 'Germany')


class DictCountryTestCase(TestCase):
    """Testing DictCountry class"""

    fixtures = ["image_app/dictcountry"]

    def setUp(self):
        # my attributes
        self.label = 'Germany'
        self.term = 'NCIT_C16636'

    def test_to_validation(self):
        """Testing specie to biosample json"""

        reference = {
            "text": self.label,
            "ontologyTerms": "/".join([
                OBO_URL,
                self.term]
            ),
        }

        germany = DictCountry.objects.get(label=self.label)
        test = germany.to_validation()

        self.assertEqual(reference, test)

    def test_to_validation_with_none(self):
        """Test to biosample conversion without term"""

        germany = DictCountry.objects.get(label=self.label)
        germany.term = None
        test = germany.to_validation()

        reference = {
            "text": self.label
        }

        self.assertEqual(reference, test)

    def test_str(self):
        """Testing str representation"""

        germany = DictCountry.objects.get(label=self.label)
        self.assertEqual(
                str(germany),
                "{label} ({term})".format(
                        label=self.label,
                        term=self.term))


class DictBreedTestCase(TestCase):
    """Testing DictBreed class"""

    fixtures = [
        "image_app/dictbreed",
        "image_app/dictcountry",
        "image_app/dictspecie"
    ]

    def test_to_validation(self):
        """Testing breed to biosample json"""

        reference = {
            "suppliedBreed": "Bunte Bentheimer",
            "country": {
                "text": "Germany",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "NCIT_C16636"]
                ),
            },
            "mappedBreed": {
                "text": "Bentheim Black Pied",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "LBO_0000347"]
                ),
            }
        }

        bunte = DictBreed.objects.get(supplied_breed='Bunte Bentheimer')
        test = bunte.to_validation()

        self.assertEqual(reference, test)

    def test_to_validation_with_none(self):
        """Test to biosample conversion without mapped objects"""

        # TODO: eval default mapped breed
        bunte = DictBreed.objects.get(supplied_breed='Bunte Bentheimer')

        # remove mapped_breed and mapped_breed_term
        bunte.mapped_breed = None
        bunte.mapped_breed_term = None

        reference = {
            "suppliedBreed": "Bunte Bentheimer",
            "country": {
                "text": "Germany",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "NCIT_C16636"]
                ),
            },
        }

        # test biosample conversion
        test = bunte.to_validation()
        self.assertEqual(reference, test)


class SubmissionTestCase(TestCase):
    """Testing Submission class"""

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/submission",
        "image_app/dictrole",
        "image_app/organization"
    ]

    def setUp(self):
        self.submission = Submission.objects.get(pk=1)

    def test_str(self):
        test = str(self.submission)
        reference = "Cryoweb (Germany, test)"

        self.assertEqual(reference, test)


class AnimalTestCase(TestCase):
    """Testing Animal Class"""

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/submission",
        "image_app/name",
        "image_app/dictbreed",
        "image_app/dictspecie",
        "image_app/dictsex",
        "image_app/animal",
        "image_app/organization",
        "image_app/dictrole",
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        # now fix person table
        person = Person.objects.get(user__username="test")
        person.affiliation_id = 1
        person.role_id = 1
        person.initials = "T"
        person.save()

    def setUp(self):
        # create animal
        self.animal = Animal.objects.get(pk=1)

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

    def test_to_validation(self):
        """Testing JSON conversion"""

        reference = {
            "biosampleId": "animal_%s" % (self.animal.id),
            "project": "IMAGE",
            "description": "a 4-year old pig organic fed",
            "material": {
                "text": "organism",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "OBI_0100026"]
                ),
            },
            "name": "ANIMAL:::ID:::132713",
            "geneBankName": "Cryoweb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "test",
            "dataSourceId": "11",
            "species": {
                "text": "Sus scrofa",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "NCBITaxon_9823"]
                ),
            },
            "breed": {
                "suppliedBreed": "Bunte Bentheimer",
                "country": {
                    "text": "Germany",
                    "ontologyTerms": "/".join([
                        OBO_URL,
                        "NCIT_C16636"]
                    ),
                },
                "mappedBreed": {
                    "text": "Bentheim Black Pied",
                    "ontologyTerms": "/".join([
                        OBO_URL,
                        "LBO_0000347"]
                    ),
                }
            },
            "sex": {
                "text": "male",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "PATO_0000384"]
                ),
            }

            # HINT: no consideration were made for father and mother
        }

        test = self.animal.to_validation()

        self.maxDiff = None
        self.assertEqual(reference, test)

    def test_to_validation_with_none(self):
        """Test to json conversion with null fields"""

        # reference with no description
        reference = {
            "biosampleId": "animal_%s" % (self.animal.id),
            "project": "IMAGE",
            "material": {
                "text": "organism",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "OBI_0100026"]
                ),
            },
            "name": "ANIMAL:::ID:::132713",
            "geneBankName": "Cryoweb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "test",
            "dataSourceId": "11",
            "species": {
                "text": "Sus scrofa",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "NCBITaxon_9823"]
                ),
            },
            "breed": {
                "suppliedBreed": "Bunte Bentheimer",
                "country": {
                    "text": "Germany",
                    "ontologyTerms": "/".join([
                        OBO_URL,
                        "NCIT_C16636"]
                    ),
                },
                "mappedBreed": {
                    "text": "Bentheim Black Pied",
                    "ontologyTerms": "/".join([
                        OBO_URL,
                        "LBO_0000347"]
                    ),
                }
            },
            "sex": {
                "text": "male",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "PATO_0000384"]
                ),
            }

            # HINT: no consideration were made for father and mother
        }

        # remove description and test
        self.animal.description = None
        self.animal.save()
        test = self.animal.to_validation()

        self.maxDiff = None
        self.assertEqual(reference, test)

    def test_to_biosample(self):
        """Testing JSON conversion for biosample submission"""

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "biosample_animal.json")
        handle = open(file_path)
        reference = json.load(handle)

        test = self.animal.to_biosample()

        self.maxDiff = None
        self.assertEqual(reference, test)

    # HINT: move to validation module?
    def test_to_biosample_minimal(self):
        """Test if biosample has biosample mininal fields"""

        validator = AnimalValidator()
        self.assertTrue(validator.check_minimal(self.animal.to_biosample()))

    def test_to_biosample_mandatory(self):
        """Test if biosample has metadata rules mandatory fields"""

        validator = AnimalValidator()
        self.assertTrue(validator.check_mandatory(self.animal.to_biosample()))

    # TODO: test None rendering


class SampleTestCase(TestCase):
    """testing sample class"""

    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/submission",
        "image_app/name",
        "image_app/dictbreed",
        "image_app/dictspecie",
        "image_app/dictsex",
        "image_app/animal",
        "image_app/sample",
        "image_app/organization",
        "image_app/dictrole",
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        # now fix person table
        person = Person.objects.get(user__username="test")
        person.affiliation_id = 1
        person.role_id = 1
        person.initials = "T"
        person.save()

    def setUp(self):
        # create animal
        self.animal = Animal.objects.get(pk=1)

        # now get a sample object
        self.sample = Sample.objects.get(pk=1)

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

    def test_to_validation(self):
        reference = {
            "biosampleId": "sample_%s" % (self.sample.id),
            "project": "IMAGE",
            "description": "semen collected when the animal turns to 4",
            "material": {
                "text": "specimen from organism",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "OBI_0001479"]
                ),
            },
            "name": "Siems_0722_393449",
            "geneBankName": "Cryoweb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "test",
            "dataSourceId": "Siems_0722_393449",
            "derivedFrom": "animal_%s" % (self.animal.id),
            "collectionDate": {
                "text": "2017-03-12",
                "unit": "YYYY-MM-DD"
            },
            "collectionPlace": "deutschland",
            "organismPart": {
                "text": "semen",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "UBERON_0001968"]
                ),
            },
            "developmentStage": {
                "text": "adult",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "EFO_0001272"]
                ),
            },
            "animalAgeAtCollection": {
                "text": 4,
                "unit": "years"
            },
            "availability": "mailto:peter@ebi.ac.uk"
        }

        test = self.sample.to_validation()

        self.maxDiff = None
        self.assertEqual(reference, test)

    def test_to_validation_with_none(self):
        """Test to biosample conversion with null fields"""

        reference = {
            "biosampleId": "sample_%s" % (self.sample.id),
            "project": "IMAGE",
            "description": "semen collected when the animal turns to 4",
            "material": {
                "text": "specimen from organism",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "OBI_0001479"]
                ),
            },
            "name": "Siems_0722_393449",
            "geneBankName": "Cryoweb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "test",
            "dataSourceId": "Siems_0722_393449",
            "derivedFrom": "animal_%s" % (self.animal.id),
        }

        # set some attributes as NULL
        self.sample.collection_date = None
        self.sample.collection_place = None
        self.sample.organism_part = None
        self.sample.organism_part_term = None
        self.sample.developmental_stage = None
        self.sample.developmental_stage_term = None
        self.sample.animal_age_at_collection = None
        self.sample.availability = None

        test = self.sample.to_validation()

        self.maxDiff = None
        self.assertEqual(reference, test)

    def test_to_biosample(self):
        """Testing JSON conversion for biosample submission"""

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "biosample_sample.json")
        handle = open(file_path)
        reference = json.load(handle)

        test = self.sample.to_biosample()

        self.maxDiff = None
        self.assertEqual(reference, test)

    # HINT: move to validation module?
    def test_to_biosample_minimal(self):
        """Test if biosample has biosample mininal fields"""

        validator = SampleValidator()
        self.assertTrue(validator.check_minimal(self.sample.to_biosample()))

    def test_to_biosample_mandatory(self):
        """Test if biosample has metadata rules mandatory fields"""

        validator = SampleValidator()
        self.assertTrue(validator.check_mandatory(self.sample.to_biosample()))

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

        test = uid_report()

        self.assertEqual(reference, test)
