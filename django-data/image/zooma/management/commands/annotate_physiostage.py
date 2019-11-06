#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 12:44:23 2019

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.core.management.base import BaseCommand
from uid.models import DictPhysioStage
from zooma.helpers import annotate_physiostage

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Call zooma for physiological stages object'

    def handle(self, *args, **options):
        # get all stage without a term
        for stage in DictPhysioStage.objects.filter(term__isnull=True):
            annotate_physiostage(stage)
