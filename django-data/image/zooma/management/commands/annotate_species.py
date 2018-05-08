#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  8 12:34:00 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging
import pprint

from django.core.management.base import BaseCommand, CommandError
from image_app.models import DictSpecie
from zooma.helpers import useZooma


# Get an instance of a logger
logger = logging.getLogger()
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console)


class Command(BaseCommand):
    help = 'Call zooma for species object'

    def handle(self, *args, **options):
        # define result
        results = {}

        # get all species without a short_term
        for specie in DictSpecie.objects.filter(short_form=None):
            results[specie.label] = useZooma(specie.label, "species")

        pprint.pprint(results)
