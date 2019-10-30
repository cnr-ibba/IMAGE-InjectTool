#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  8 12:34:00 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.core.management.base import BaseCommand
from uid.models import DictSpecie
from zooma.helpers import annotate_specie

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Call zooma for species object'

    def handle(self, *args, **options):
        # get all species without a term
        for specie in DictSpecie.objects.filter(term__isnull=True):
            annotate_specie(specie)
