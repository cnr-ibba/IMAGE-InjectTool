#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 11:59:47 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import logging

from decouple import AutoConfig
from django.conf import settings
from django.core.management import BaseCommand

from biosample.models import ManagedTeam
from biosample.helpers import get_manager_auth

# Get an instance of a logger
logger = logging.getLogger(__name__)

# change the default level for pyUSIrest logging
logging.getLogger('pyUSIrest.auth').setLevel(logging.INFO)
logging.getLogger('pyUSIrest.client').setLevel(logging.INFO)
logging.getLogger('pyUSIrest.usi').setLevel(logging.INFO)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


class Command(BaseCommand):
    help = 'Fill biosample managed teams table'

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Called fill_managed to fill biosamples managed teams")

        # create a new auth object
        auth = get_manager_auth()

        for domain in auth.get_domains():
            managed, created = ManagedTeam.objects.get_or_create(
                name=domain)

            if created is True:
                logger.info("Created: %s" % (managed))

        # completed
        logger.info("fill_managed ended")
