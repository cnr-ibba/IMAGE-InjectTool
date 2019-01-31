#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 15:28:05 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

This django command script need to be called after database initialization.
The aim is to fill tables like ontology tables (roles, sex) in order to upload
data from cryoweb database (or xls template files, or ...)
"""

import collections
import csv
import io
import logging
import os

from django.core.management import BaseCommand

from image_app.models import (DictCountry, DictRole, DictSex, DictSpecie,
                              Ontology, Organization, CONFIDENCES)
from language.models import SpecieSynonim

# Get an instance of a logger
logger = logging.getLogger(__name__)


def fill_ontology():
    data = """Library name;Library URI;Comment
PATO;http://purl.obolibrary.org/obo;Phenotype And Trait Ontology
LBO;http://purl.obolibrary.org/obo;Livestock Breed Ontology
EFO;http://www.ebi.ac.uk/efo;Experimental Factor Ontology
OBI;http://purl.obolibrary.org/obo;Ontology for Biomedical Investigations
NCBITaxon;http://purl.obolibrary.org/obo;NCBI Taxonomy
UBERON;http://purl.obolibrary.org/obo;cross-species ontology covering anatomical structures in animals
GAZ;http://purl.obolibrary.org/obo;A gazetteer constructed on ontological principles
NCIT;http://purl.obolibrary.org/obo;NCI Thesaurus OBO Edition
"""

    handle = io.StringIO(data)
    reader = csv.reader(handle, delimiter=";")

    header = next(reader)

    # fix header
    header = [col.lower().replace(" ", "_") for col in header]

    Data = collections.namedtuple('Data', header)

    for row in map(Data._make, reader):
        # update objects
        ontology, created = Ontology.objects.update_or_create(
                library_name=row.library_name,
                defaults=row._asdict())

        if created is True:
            logger.info("Created: %s" % (ontology))


def fill_DictSex():
    # define two DictSex objects
    male, created = DictSex.objects.get_or_create(
        label='male', term='PATO_0000384')

    if created is True:
        logger.info("Created: %s" % (male))

    female, created = DictSex.objects.get_or_create(
        label='female', term='PATO_0000383')

    if created is True:
        logger.info("Created: %s" % (female))


# a function to fill up DictRoles
def fill_DictRoles():
    # define a submitter role
    role, created = DictRole.objects.get_or_create(
        label='submitter', term='EFO_0001741')

    if created is True:
        logger.info("Created: %s" % (role))

    return role


# a function to fill up dictspecie and speciesynonim
def fill_Species():
    """Populate cryoweb dictionary tables"""

    # insert country
    language = fill_Countries()

    # those are cryoweb DE species an synonims
    cryoweb = {
        'Cattle': 'Bos taurus',
        'Chicken': 'Gallus gallus',
        'Deer': 'Cervidae',
        'Duck (domestic)': 'Anas platyrhynchos',
        'Goat': 'Capra hircus',
        'Goose (domestic)': 'Anser anser',
        'Horse': 'Equus caballus',
        'Pig': 'Sus scrofa',
        'Rabbit': 'Oryctolagus cuniculus',
        'Sheep': 'Ovis aries',
        'Turkey': 'Meleagris gallopavo'
    }

    for word, specie in cryoweb.items():
        dictspecie, created = DictSpecie.objects.get_or_create(
            label=specie)

        if created is True:
            logger.info("Created: %s" % (specie))

        synonim, created = SpecieSynonim.objects.get_or_create(
            dictspecie=dictspecie,
            language=language,
            word=word)

        if created is True:
            logger.info("Created: %s" % (synonim))


def fill_Countries():
    # define the default country for the default language
    country, created = DictCountry.objects.get_or_create(
        label='United Kingdom',
        term='NCIT_C17233',
        confidence=CONFIDENCES.get_value('curated'))

    if created is True:
        logger.info("Created: %s" % (country))

    return country


def fill_Organization():
    """Fill organization table"""

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filename = os.path.join(base_dir, "commands/organization_list.csv")

    # open data file
    handle = open(filename)
    reader = csv.reader(handle, delimiter=";")
    Data = collections.namedtuple('Data', "id name country")

    # get a role
    role = fill_DictRoles()

    for row in map(Data._make, reader):
        # get a country object
        country, created = DictCountry.objects.get_or_create(
            label=row.country)

        if created is True:
            logger.info("Created: %s" % (country))

        organization, created = Organization.objects.get_or_create(
            name=row.name, role=role, country=country)

        if created is True:
            logger.info("Created: %s" % (organization))

    handle.close()


class Command(BaseCommand):
    help = 'Fill database tables like roles, sex, etc'

    def handle(self, *args, **options):
        # call commands and fill tables.
        fill_ontology()

        # Fill sex tables
        fill_DictSex()

        # fill DictRoles table
        fill_DictRoles()

        # import synonims
        fill_Species()

        # import organizations
        fill_Organization()
