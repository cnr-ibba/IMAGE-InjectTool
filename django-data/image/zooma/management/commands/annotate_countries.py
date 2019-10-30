#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  9 11:21:45 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.core.management.base import BaseCommand
from uid.models import DictCountry
from zooma.helpers import annotate_country

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Call zooma for species object'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            default=False,
            help="Annotate all countries")

    def handle(self, *args, **options):
        if options['all']:
            # finalize submission if there are not errors
            logger.info("Updating all countries")
            for country in DictCountry.objects.all():
                annotate_country(country)

        else:
            logger.info("Updating countries without terms")
            # get all countries without a term
            for country in DictCountry.objects.filter(term__isnull=True):
                annotate_country(country)

        logger.info("Done!")
