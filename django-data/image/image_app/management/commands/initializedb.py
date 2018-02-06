#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 15:28:05 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

This django command script need to be called after database initialization.
The aim is to fill tables like ontology tables (roles, sex) in order to upload
data from cryoweb database (or xls template files, or ...)
"""

from django.core.management import BaseCommand

from image_app.models import DictSex


def fill_DictSex():
    # define two DictSex objects
    male, created = DictSex.objects.get_or_create(
            label='male', short_form='PATO_0000384')

    if created is True:
        print("Created: %s" % (male))

    female, created = DictSex.objects.get_or_create(
            label='female', short_form='PATO_0000383')

    if created is True:
        print("Created: %s" % (female))


# TODO: define a function to fill up DictRoles


class Command(BaseCommand):
    help = 'Fill database tables like roles, sex, etc'

    def handle(self, *args, **options):
        # call commands and fill tables. Fill sex tables
        fill_DictSex()
