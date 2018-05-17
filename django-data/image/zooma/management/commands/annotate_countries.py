#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  9 11:21:45 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging
import pprint

from django.core.management.base import BaseCommand
from image_app.models import DictCountry
from zooma.helpers import useZooma

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Call zooma for species object'

    def handle(self, *args, **options):
        # define result
        results = {}

        # get all species without a short_term
        for country in DictCountry.objects.filter(term=None):
            results[country.label] = useZooma(country.label, "country")

        pprint.pprint(results)
