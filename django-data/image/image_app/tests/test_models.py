#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 12:16:55 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import datetime

from django.test import TestCase

from image_app.models import (Animal, DataSource, DictBreed, DictCountry,
                              DictSex, DictSpecie, Name, Sample, uid_report)


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


def create_datasource():
    # get dependencies
    country = create_dictcountry()

    ds, created = DataSource.objects.get_or_create(
                name='CryoWeb',
                version='23.01',
                type=0,  # CryoWeb
                country=country)

    return ds


def create_animal():
    ds = create_datasource()

    name, created = Name.objects.get_or_create(
            name='ANIMAL:::ID:::132713',
            datasource=ds)

    breed = create_dictbreed()

    sex = create_dictsex()

    animal, created = Animal.objects.get_or_create(
            name=name,
            alternative_id=11,
            description="a 4-year old pig organic fed",
            breed=breed,
            sex=sex)

    # record id
    return animal


def create_sample(animal):
    # get current datasource for a new name
    ds = create_datasource()

    name, created = Name.objects.get_or_create(
            name='Siems_0722_393449',
            datasource=ds)

    # now create a sample object
    sample, created = Sample.objects.get_or_create(
            name=name,
            alternative_id='Siems_0722_393449',
            description="semen collected when the animal turns to 4",
            animal=animal,
            collection_date=datetime.date(2017, 3, 12),
            collection_place="deutschland",
            organism_part='semen',
            organism_part_ontology_accession='UBERON_0001968',
            developmental_stage='adult',
            developmental_stage_ontology_accession='EFO_0001272',
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

    def test_to_biosample(self):
        """Testing sex to biosample json"""

        reference = {
            "text": self.label,
            "ontologyTerms": self.term
        }

        male = DictSex.objects.get(label=self.label)
        test = male.to_biosample()

        self.assertEqual(reference, test)

    def test_to_biosample_with_none(self):
        """Test to biosample conversion without term"""

        male = DictSex.objects.get(label=self.label)
        male.term = None
        test = male.to_biosample()

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

    def test_to_biosample(self):
        """Testing specie to biosample json"""

        reference = {
                "text": self.label,
                "ontologyTerms": self.term
        }

        sus = DictSpecie.objects.get(label=self.label)
        test = sus.to_biosample()

        self.assertEqual(reference, test)

    def test_to_biosample_with_none(self):
        """Test to biosample conversion without term"""

        sus = DictSpecie.objects.get(label=self.label)
        sus.term = None
        test = sus.to_biosample()

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


class DictCountryTestCase(TestCase):
    """Testing DictCountry class"""

    def setUp(self):
        # my attributes
        self.label = 'Germany'
        self.term = 'NCIT_C16636'

        # call an helper function
        create_dictcountry(label=self.label, term=self.term)

    def test_to_biosample(self):
        """Testing specie to biosample json"""

        reference = {
                "text": self.label,
                "ontologyTerms": self.term
        }

        germany = DictCountry.objects.get(label=self.label)
        test = germany.to_biosample()

        self.assertEqual(reference, test)

    def test_to_biosample_with_none(self):
        """Test to biosample conversion without term"""

        germany = DictCountry.objects.get(label=self.label)
        germany.term = None
        test = germany.to_biosample()

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

    def test_to_biosample(self):
        """Testing breed to biosample json"""

        reference = {
            "suppliedBreed": "Bunte Bentheimer",
            "country": {
                "text": "Germany",
                "ontologyTerms": "NCIT_C16636"
            },
            "mappedBreed": {
                "text": "Bentheim Black Pied",
                "ontologyTerms": "LBO_0000347"
            }
        }

        bunte = DictBreed.objects.get(supplied_breed='Bunte Bentheimer')
        test = bunte.to_biosample()

        self.assertEqual(reference, test)

    def test_to_biosample_with_none(self):
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
                "ontologyTerms": "NCIT_C16636"
            },
        }

        # test biosample conversion
        test = bunte.to_biosample()
        self.assertEqual(reference, test)


class DataSourceTestCase(TestCase):
    """Testing DataSource class"""

    def setUp(self):
        # call an helper function
        self.datasource = create_datasource()

    def test_str(self):
        test = str(self.datasource)
        reference = "CryoWeb (Germany, 23.01)"

        self.assertEqual(reference, test)


class AnimalTestCase(TestCase):
    """Testing Animal Class"""

    def setUp(self):
        # create animal
        animal = create_animal()

        # record id
        self.animal_id = animal.id

    def test_get_biosample_id(self):
        """Get a biosample id or a temporary id"""

        animal = Animal.objects.get(name__name='ANIMAL:::ID:::132713')
        reference = "animal_%s" % (animal.id)

        test = animal.get_biosample_id()
        self.assertEqual(reference, test)

        # assign a different biosample id
        reference = "SAMEA4450079"
        animal.name.biosample_id = reference
        animal.save()

        test = animal.get_biosample_id()
        self.assertEqual(reference, test)

    def test_to_biosample(self):
        """Testing JSON conversion"""

        reference = {
            "biosampleId": "animal_%s" % (self.animal_id),
            "project": "IMAGE",
            "description": "a 4-year old pig organic fed",
            "material": {
                "text": "organism",
                "ontologyTerms": "OBI_0100026"
            },
            "name": "ANIMAL:::ID:::132713",
            "geneBankName": "CryoWeb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "23.01",
            "dataSourceId": "11",
            "species": {
                "text": "Sus scrofa",
                "ontologyTerms": "NCBITaxon_9823"
            },
            "breed": {
                "suppliedBreed": "Bunte Bentheimer",
                "country": {
                    "text": "Germany",
                    "ontologyTerms": "NCIT_C16636"
                },
                "mappedBreed": {
                    "text": "Bentheim Black Pied",
                    "ontologyTerms": "LBO_0000347"
                }
            },
            "sex": {
                "text": "male",
                "ontologyTerms": "PATO_0000384"
            }

            # HINT: no consideration were made for father and mother
        }

        animal = Animal.objects.get(name__name='ANIMAL:::ID:::132713')
        test = animal.to_biosample()

        self.maxDiff = None
        self.assertEqual(reference, test)

    def test_to_biosample_with_none(self):
        """Test to biosample conversion with null fields"""

        # reference with no description
        reference = {
            "biosampleId": "animal_%s" % (self.animal_id),
            "project": "IMAGE",
            "material": {
                "text": "organism",
                "ontologyTerms": "OBI_0100026"
            },
            "name": "ANIMAL:::ID:::132713",
            "geneBankName": "CryoWeb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "23.01",
            "dataSourceId": "11",
            "species": {
                "text": "Sus scrofa",
                "ontologyTerms": "NCBITaxon_9823"
            },
            "breed": {
                "suppliedBreed": "Bunte Bentheimer",
                "country": {
                    "text": "Germany",
                    "ontologyTerms": "NCIT_C16636"
                },
                "mappedBreed": {
                    "text": "Bentheim Black Pied",
                    "ontologyTerms": "LBO_0000347"
                }
            },
            "sex": {
                "text": "male",
                "ontologyTerms": "PATO_0000384"
            }

            # HINT: no consideration were made for father and mother
        }

        animal = Animal.objects.get(name__name='ANIMAL:::ID:::132713')

        # remove description and test
        animal.description = None
        test = animal.to_biosample()

        self.maxDiff = None
        self.assertEqual(reference, test)


class SampleTestCase(TestCase):
    """testing sample class"""

    def setUp(self):
        # create animal
        animal = create_animal()

        # record id for the animal
        self.animal_id = animal.id

        # now create a sample object
        sample = create_sample(animal)

        self.sample_id = sample.id

    def test_get_biosample_id(self):
        """Get a biosample id or a temporary id"""

        sample = Sample.objects.get(name__name="Siems_0722_393449")
        reference = "sample_%s" % (sample.id)

        test = sample.get_biosample_id()
        self.assertEqual(reference, test)

        # assign a different biosample id
        reference = "SAMEA4450075"
        sample.name.biosample_id = reference
        sample.save()

        test = sample.get_biosample_id()
        self.assertEqual(reference, test)

    def test_to_biosample(self):
        reference = {
            "biosampleId": "sample_%s" % (self.sample_id),
            "project": "IMAGE",
            "description": "semen collected when the animal turns to 4",
            "material": {
                "text": "specimen from organism",
                "ontologyTerms": "OBI_0001479"
            },
            "geneBankName": "CryoWeb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "23.01",
            "dataSourceId": "Siems_0722_393449",
            "derivedFrom": "animal_%s" % (self.animal_id),
            "name": "Siems_0722_393449",
            "collectionDate": {
                "text": "2017-03-12",
                "unit": "YYYY-MM-DD"
            },
            "collectionPlace": "deutschland",
            "organismPart": {
                "text": "semen",
                "ontologyTerms": "UBERON_0001968"
            },
            "developmentStage": {
                "text": "adult",
                "ontologyTerms": "EFO_0001272"
            },
            "animalAgeAtCollection": {
                "text": 4,
                "unit": "years"
            },
            "availability": "mailto:peter@ebi.ac.uk"
        }

        sample = Sample.objects.get(name__name='Siems_0722_393449')
        test = sample.to_biosample()

        self.maxDiff = None
        self.assertEqual(reference, test)

    def test_to_biosample_with_none(self):
        """Test to biosample conversion with null fields"""

        reference = {
            "biosampleId": "sample_%s" % (self.sample_id),
            "project": "IMAGE",
            "description": "semen collected when the animal turns to 4",
            "material": {
                "text": "specimen from organism",
                "ontologyTerms": "OBI_0001479"
            },
            "geneBankName": "CryoWeb",
            "geneBankCountry": "Germany",
            "dataSourceType": "CryoWeb",
            "dataSourceVersion": "23.01",
            "dataSourceId": "Siems_0722_393449",
            "derivedFrom": "animal_%s" % (self.animal_id),
            "name": "Siems_0722_393449",
        }

        sample = Sample.objects.get(name__name='Siems_0722_393449')

        # set some attributes as NULL
        sample.collection_date = None
        sample.collection_place = None
        sample.organism_part = None
        sample.organism_part_ontology_accession = None
        sample.developmental_stage = None
        sample.developmental_stage_ontology_accession = None
        sample.animal_age_at_collection = None
        sample.availability = None

        test = sample.to_biosample()

        self.maxDiff = None
        self.assertEqual(reference, test)

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
