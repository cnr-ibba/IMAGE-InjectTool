#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  9 11:25:09 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging
import pprint

from django.core.management.base import BaseCommand
from image_app.models import DictBreed
from zooma.helpers import useZooma


# Get an instance of a logger and set a debug level
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

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
        for breed in DictBreed.objects.filter(mapped_breed=None):
            results[breed.supplied_breed] = useZooma(
                breed.supplied_breed, "breed")

        pprint.pprint(results)
