#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  9 11:25:09 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.core.management.base import BaseCommand
from image_app.models import DictUberon
from zooma.helpers import annotate_uberon

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Call zooma for dictbreed object. Fill table if possible'

    def handle(self, *args, **options):
        # get all species without a term
        for part in DictUberon.objects.filter(term__isnull=True):
            annotate_uberon(part)
