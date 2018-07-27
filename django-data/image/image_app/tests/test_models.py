#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 12:16:55 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import datetime

from django.test import TestCase

from image_app.models import (Animal, Submission, DictBreed, DictCountry,
                              DictSex, DictSpecie, Name, Sample, uid_report)
from language.models import SpecieSynonim

from validation.helpers.biosample import AnimalValidator, SampleValidator

from ..constants import OBO_URL


# a series of helper functions
def create_dictsex(label='male', term='PATO_0000384'):
    sex, created = DictSex.objects.get_or_create(
                label=label,
                term=term)

    return sex


def create_dictspecie(label='Sus scrofa', term='NCBITaxon_9823'):
    specie, created = DictSpecie.objects.get_or_create(
                label=label,
                term=term)

    # get a country
    country = create_dictcountry()

    # create a synonim
    synonim, created = SpecieSynonim.objects.get_or_create(
        dictspecie=specie,
        language=country,
        word='Pig')

    return specie


def create_dictcountry(label='Germany', term='NCIT_C16636'):
    country, created = DictCountry.objects.get_or_create(
                label=label,
                term=term)

    return country


def create_dictbreed():
    specie = create_dictspecie()

    country = create_dictcountry()

    breed, created = DictBreed.objects.get_or_create(
                supplied_breed='Bunte Bentheimer',
                mapped_breed='Bentheim Black Pied',
                mapped_breed_term='LBO_0000347',
                country=country,
                specie=specie)

    return breed


def create_submission():
    # get dependencies
    country = create_dictcountry()

    submission, created = Submission.objects.get_or_create(
                gene_bank_name='CryoWeb',
                datasource_version='23.01',
                datasource_type=0,  # CryoWeb
                gene_bank_country=country)

    return submission


def create_animal():
    submission = create_submission()

    name, created = Name.objects.get_or_create(
            name='ANIMAL:::ID:::132713',
            submission=submission)

    breed = create_dictbreed()

    sex = create_dictsex()

    animal, created = Animal.objects.get_or_create(
            name=name,
            alternative_id='11',
            description="a 4-year old pig organic fed",
            breed=breed,
            sex=sex)

    # record id
    return animal


def create_sample(animal):
    # get current submission for a new name
    submission = create_submission()

    name, created = Name.objects.get_or_create(
            name='Siems_0722_393449',
            submission=submission)

    # now create a sample object
    sample, created = Sample.objects.get_or_create(
            name=name,
            alternative_id='Siems_0722_393449',
            description="semen collected when the animal turns to 4",
            animal=animal,
            collection_date=datetime.date(2017, 3, 12),
            collection_place="deutschland",
            organism_part='semen',
            organism_part_term='UBERON_0001968',
            developmental_stage='adult',
            developmental_stage_term='EFO_0001272',
            animal_age_at_collection=4,
            availability='mailto:peter@ebi.ac.uk')

    return sample


class DictSexTestCase(TestCase):
    """Testing DictSex class"""

    def setUp(self):
        # my attributes
        self.label = 'male'
        self.term = 'PATO_0000384'

        # call an helper function
        create_dictsex(label=self.label, term=self.term)

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

    def setUp(self):
        # my attributes
        self.label = 'Sus scrofa'
        self.term = 'NCBITaxon_9823'

        # call an helper function
        create_dictspecie(label=self.label, term=self.term)

    def test_to_validation(self):
        """Testing specie to biosample json"""

        reference = {
            "text": self.label,
            "ontologyTerms": "/".join([
                OBO_URL,
                self.term]
            ),
        }

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

    def setUp(self):
        # my attributes
        self.label = 'Germany'
        self.term = 'NCIT_C16636'

        # call an helper function
        create_dictcountry(label=self.label, term=self.term)

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

    def setUp(self):
        # call an helper function
        create_dictbreed()

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

    def setUp(self):
        # call an helper function
        self.submission = create_submission()

    def test_str(self):
        test = str(self.submission)
        reference = "CryoWeb (Germany, 23.01)"

        self.assertEqual(reference, test)


class AnimalTestCase(TestCase):
    """Testing Animal Class"""

    def setUp(self):
        # create animal
        self.animal = create_animal()

        # record id
        self.animal_id = self.animal.id

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
            "biosampleId": "animal_%s" % (self.animal_id),
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
            "geneBankName": "CryoWeb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "23.01",
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
            "biosampleId": "animal_%s" % (self.animal_id),
            "project": "IMAGE",
            "material": {
                "text": "organism",
                "ontologyTerms": "/".join([
                    OBO_URL,
                    "OBI_0100026"]
                ),
            },
            "name": "ANIMAL:::ID:::132713",
            "geneBankName": "CryoWeb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "23.01",
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

        reference = {
            'alias': "animal_%s" % (self.animal_id),
            'title': 'ANIMAL:::ID:::132713',
            'releaseDate': str(datetime.datetime.now().date()),
            'taxonId': 9823,
            'description': "a 4-year old pig organic fed",
            'attributes': {},
            'sampleRelationships': []
        }

        # define attributes
        attributes = {
            "material": [{
                "value": "organism",
                "terms": [{
                    "url": "/".join([
                        OBO_URL,
                        "OBI_0100026"])
                }]
            }],
            "project": [{
                "value": "IMAGE"
            }],
        }

        reference['attributes'] = attributes

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

    def setUp(self):
        # create animal
        self.animal = create_animal()

        # record id for the animal
        self.animal_id = self.animal.id

        # now create a sample object
        self.sample = create_sample(self.animal)

        self.sample_id = self.sample.id

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
            "biosampleId": "sample_%s" % (self.sample_id),
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
            "geneBankName": "CryoWeb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "23.01",
            "dataSourceId": "Siems_0722_393449",
            "derivedFrom": "animal_%s" % (self.animal_id),
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
            "biosampleId": "sample_%s" % (self.sample_id),
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
            "geneBankName": "CryoWeb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "23.01",
            "dataSourceId": "Siems_0722_393449",
            "derivedFrom": "animal_%s" % (self.animal_id),
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

        reference = {
            'alias': "sample_%s" % (self.sample_id),
            'title': 'Siems_0722_393449',
            'releaseDate': str(datetime.datetime.now().date()),
            'taxonId': 9823,
            'description': "semen collected when the animal turns to 4",
            'attributes': {},
            'sampleRelationships': [{
                "alias": "animal_%s" % (self.animal_id),
                "relationshipNature": "derived from"
            }]
        }

        # define attributes
        attributes = {
            "material": [{
                "value": "specimen from organism",
                "terms": [{
                    "url": "/".join([
                        OBO_URL,
                        "OBI_0001479"])
                }]
            }],
            "project": [{
                "value": "IMAGE"
            }],
        }

        reference['attributes'] = attributes

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
