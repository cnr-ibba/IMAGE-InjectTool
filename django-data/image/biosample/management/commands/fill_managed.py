#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 11:59:47 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import sys
import logging

from decouple import AutoConfig
from django.conf import settings
from django.core.management import BaseCommand

from pyEBIrest.auth import Auth

from biosample.models import ManagedTeam

# Get an instance of a logger
logger = logging.getLogger(__name__)

# change the default level for pyEBIrest logging
logging.getLogger('pyEBIrest.auth').setLevel(logging.INFO)
logging.getLogger('pyEBIrest.client').setLevel(logging.INFO)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


class Command(BaseCommand):
    help = 'Fill biosample managed teams table'

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Called %s" % (sys.argv[1]))

        # create a new auth object
        auth = Auth(
            user=config('USI_MANAGER'),
            password=config('USI_MANAGER_PASSWORD'))

        for domain in auth.claims['domains']:
            managed, created = ManagedTeam.objects.get_or_create(
                team_name=domain)

            if created is True:
                logger.info("Created: %s" % (managed))

        # completed
        logger.info("%s ended" % (sys.argv[1]))
