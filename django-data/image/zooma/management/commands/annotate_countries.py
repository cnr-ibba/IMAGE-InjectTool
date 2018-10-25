#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  9 11:21:45 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.core.management.base import BaseCommand
from image_app.models import DictCountry
from zooma.helpers import annotate_country

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Call zooma for species object'

    def handle(self, *args, **options):
        # get all countries without a term
        for country in DictCountry.objects.filter(term__isnull=True):
            annotate_country(country)
