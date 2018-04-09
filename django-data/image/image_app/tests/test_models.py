#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 12:16:55 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import datetime

from django.test import TestCase

from image_app.models import (Animal, DataSource, DictBreed, DictSex, Name,
                              Sample)


class DictSexTestCase(TestCase):
    """Testing DictSex class"""

    def setUp(self):
        DictSex.objects.create(
                label='male', short_form='PATO_0000384')

    def test_to_biosample(self):
        """Testing sex to biosample json"""

        reference = {
            "text": "male",
            "ontologyTerms": "PATO_0000384"
        }

        male = DictSex.objects.get(label="male")
        test = male.to_biosample()

        self.assertEqual(reference, test)


class DictBreedTestCase(TestCase):
    """Testing DictBreed class"""

    def setUp(self):
        DictBreed.objects.create(
                supplied_breed='Bunte Bentheimer',
                mapped_breed='Bentheim Black Pied',
                mapped_breed_ontology_accession='LBO_0000347',
                country='Germany',
                country_ontology_accession='NCIT_C16636',
                species='Sus scrofa',
                species_ontology_accession='NCBITaxon_9823')

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


class AnimalTestCase(TestCase):
    """Testing Animal Class"""

    def setUp(self):
        ds = DataSource.objects.create(
                name='CryoWeb DE',
                version='23.01')

        name = Name.objects.create(
                name='ANIMAL:::ID:::132713',
                datasource=ds)

        breed = DictBreed.objects.create(
                supplied_breed='Bunte Bentheimer',
                mapped_breed='Bentheim Black Pied',
                mapped_breed_ontology_accession='LBO_0000347',
                country='Germany',
                country_ontology_accession='NCIT_C16636',
                species='Sus scrofa',
                species_ontology_accession='NCBITaxon_9823')

        sex = DictSex.objects.create(
                label='male', short_form='PATO_0000384')

        animal = Animal.objects.create(
                name=name,
                alternative_id=11,
                description="a 4-year old pig organic fed",
                breed=breed,
                sex=sex)

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
            "dataSourceName": "CryoWeb DE",
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


class SampleTestCase(TestCase):
    """testing sample class"""

    def setUp(self):
        ds = DataSource.objects.create(
                name='CryoWeb DE',
                version='23.01')

        name = Name.objects.create(
                name='Siems_0722_393449',
                datasource=ds)

        # create an animal first
        breed = DictBreed.objects.create(
                supplied_breed='Bunte Bentheimer',
                mapped_breed='Bentheim Black Pied',
                mapped_breed_ontology_accession='LBO_0000347',
                country='Germany',
                country_ontology_accession='NCIT_C16636',
                species='Sus scrofa',
                species_ontology_accession='NCBITaxon_9823')

        sex = DictSex.objects.create(
                label='male', short_form='PATO_0000384')

        animal = Animal.objects.create(
                name=name,
                alternative_id=11,
                description="a 4-year old pig organic fed",
                breed=breed,
                sex=sex)

        # record id for the animal
        self.animal_id = animal.id

        # now create a sample object
        sample = Sample.objects.create(
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
            "dataSourceName": "CryoWeb DE",
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