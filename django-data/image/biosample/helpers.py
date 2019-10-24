#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 12:13:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import logging

from decouple import AutoConfig

import pyUSIrest.auth

from django.conf import settings

# Get an instance of a logger
logger = logging.getLogger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


def get_auth(user=None, password=None, token=None):
    """Returns an Auth instance"""

    # instantiate an Auth object if a token is provieded
    if token:
        return pyUSIrest.auth.Auth(token=token)

    return pyUSIrest.auth.Auth(user, password)


def get_manager_auth():
    """Get an Auth object for imagemanager user"""

    return get_auth(
        user=config('USI_MANAGER'),
        password=config('USI_MANAGER_PASSWORD'))
