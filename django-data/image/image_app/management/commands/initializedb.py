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

from django.core.management import BaseCommand

from image_app.models import DictRole, DictSex, Ontology

# Get an instance of a logger
logger = logging.getLogger(__name__)


def fill_ontology():
    data = """Library name;Library URI;Comment
PATO;http://www.ebi.ac.uk/ols/ontologies/pato;Phenotype And Trait Ontology
LBO;http://www.ebi.ac.uk/ols/ontologies/lbo;Livestock Breed Ontology
EFO;http://www.ebi.ac.uk/ols/ontologies/efo;Experimental Factor Ontology
OBI;http://www.ebi.ac.uk/ols/ontologies/obi;Ontology for Biomedical Investigations
NCBITaxon;http://www.ebi.ac.uk/ols/ontologies/ncbitaxon;NCBI Taxonomy
UBERON;http://www.ebi.ac.uk/ols/ontologies/uberon;cross-species ontology covering anatomical structures in animals
GAZ;https://www.ebi.ac.uk/ols/ontologies/gaz;A gazetteer constructed on ontological principles
"""

    handle = io.StringIO(data)
    reader = csv.reader(handle, delimiter=";")

    header = next(reader)

    # fix header
    header = [col.lower().replace(" ", "_") for col in header]

    Data = collections.namedtuple('Data', header)

    for row in map(Data._make, reader):
        ontology, created = Ontology.objects.get_or_create(**row._asdict())

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


# a function to fill up dictspecie and speciesynonim
def fill_Species():
    pass


class Command(BaseCommand):
    help = 'Fill database tables like roles, sex, etc'

    def handle(self, *args, **options):
        # call commands and fill tables.
        fill_ontology()

        # Fill sex tables
        fill_DictSex()

        # fill DictRoles table
        fill_DictRoles()
