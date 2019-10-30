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

from image_validation.use_ontology import get_general_breed_by_species

from django.core.management import BaseCommand

from common.constants import OBO_URL, CURATED
from uid.models import (
    DictCountry, DictRole, DictSex, DictSpecie, Ontology, Organization,
    DictUberon)
from language.models import SpecieSynonym

# Get an instance of a logger
logger = logging.getLogger(__name__)


def fill_ontology():
    data = """Library name;Library URI;Comment
PATO;{obo_url};Phenotype And Trait Ontology
LBO;{obo_url};Livestock Breed Ontology
EFO;http://www.ebi.ac.uk/efo;Experimental Factor Ontology
OBI;{obo_url};Ontology for Biomedical Investigations
NCBITaxon;{obo_url};NCBI Taxonomy
UBERON;{obo_url};cross-species ontology covering anatomical structures in animals
GAZ;{obo_url};A gazetteer constructed on ontological principles
NCIT;{obo_url};NCI Thesaurus OBO Edition
""".format(obo_url=OBO_URL)

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
    # define three DictSex objects
    male, created = DictSex.objects.get_or_create(
        label='male', term='PATO_0000384')

    if created is True:
        logger.info("Created: %s" % (male))

    female, created = DictSex.objects.get_or_create(
        label='female', term='PATO_0000383')

    if created is True:
        logger.info("Created: %s" % (female))

    unknown, created = DictSex.objects.get_or_create(
        label='record of unknown sex', term='OBI_0000858')

    if created is True:
        logger.info("Created: %s" % (unknown))


# a function to fill up DictRoles
# TODO: need I fill tables with descendants terms?
def fill_DictRoles():
    # define a submitter role
    role, created = DictRole.objects.get_or_create(
        label='submitter', term='EFO_0001741')

    if created is True:
        logger.info("Created: %s" % (role))

    return role


# a function to fill up dictspecie and speciesynonym
def fill_Species():
    """Populate cryoweb dictionary tables"""

    # insert country and get the default language
    language = fill_Countries()

    # those are cryoweb DE species an synonyms
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

        # update with general specie
        result = get_general_breed_by_species(specie)

        if result != {}:
            general_breed_label = result['text']
            # split the full part and get the last piece
            general_breed_term = result['ontologyTerms'].split("/")[-1]

            if dictspecie.general_breed_label != general_breed_label:
                logger.info("Added general breed: %s" % (general_breed_label))
                dictspecie.general_breed_label = general_breed_label
                dictspecie.general_breed_term = general_breed_term
                dictspecie.save()

        synonym, created = SpecieSynonym.objects.get_or_create(
            dictspecie=dictspecie,
            language=language,
            word=word)

        if created is True:
            logger.info("Created: %s" % (synonym))


def fill_Countries():
    """Fill countries and return the default country (for languages)"""

    # define the default country for the default language
    united_kingdom, created = DictCountry.objects.get_or_create(
        label='United Kingdom',
        term='NCIT_C17233',
        confidence=CURATED)

    if created is True:
        logger.info("Created: %s" % (united_kingdom))

    # add a country difficult to annotate with zooma
    country, created = DictCountry.objects.get_or_create(
        label='Colombia',
        term='NCIT_C16449',
        confidence=CURATED)

    if created is True:
        logger.info("Created: %s" % (country))

    # I will return default language for translations
    return united_kingdom


def fill_OrganismParts():
    """Fill organism parts with manually curated terms"""

    data = {'strand of hair': "UBERON_0001037"}

    for label, term in data.items():
        dictorganism, created = DictUberon.objects.get_or_create(
            label=label,
            term=term,
            confidence=CURATED
        )

        if created is True:
            logger.info("Created: %s" % (dictorganism))


def standardize_institute_name(original):
    special = {
        'de': 1,
        'la': 1,
        'of': 1,
        'and': 1,
        'y': 1,
        'fuer': 1,
        'del': 1,
        'l': 1,
        'INRA': 1,
        'FAO': 1
    }

    # search space in original (instutute name) if no space is found
    # it is like that institute name will be EBI or IBBA, and will be
    # treated as it is
    if original.find(" ") > -1:
        if original.upper() == original:
            components = original.split(' ')
            # We capitalize the first letter of each component except the first
            # one with the 'title' method and join them together.
            result = ''
            for component in components:
                result = result + ' '
                if component.lower() in special:
                    result = result + component.lower()
                elif component.upper() in special:
                    result = result + component.upper()
                else:
                    result = result + component.title()
            result = result[1:]
            return result
    return original


def fill_Organization():
    """Fill organization table"""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(base_dir, "organization_list.csv")

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

        # HINT: could be better to fix organization names in organization_list?
        organization, created = Organization.objects.get_or_create(
            name=standardize_institute_name(row.name),
            role=role,
            country=country)

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

        # import synonyms
        fill_Species()

        # import organizations
        fill_Organization()

        # import organisms
        fill_OrganismParts()
