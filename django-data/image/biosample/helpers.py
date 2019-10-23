#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 12:13:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os

from decouple import AutoConfig

from pyUSIrest.auth import Auth

from django.conf import settings


# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)

# read biosample URLs from configuration file
EBI_AUTH_URL = config(
    'EBI_AUTH_URL', default="https://explore.api.aai.ebi.ac.uk/auth")
BIOSAMPLE_API_ROOT = config(
    'BIOSAMPLE_API_ROOT', default="https://submission-test.ebi.ac.uk/api/")

# Ovveride Auth.auth_url
Auth.auth_url = EBI_AUTH_URL


def get_auth(user=None, password=None, token=None):
    """Returns an Auth instance"""

    # instantiate an Auth object if a token is provieded
    if token:
        return Auth(token=token)

    return Auth(user, password)


def get_manager_auth():
    """Get an Auth object for imagemanager user"""

    return get_auth(
        user=config('USI_MANAGER'),
        password=config('USI_MANAGER_PASSWORD'))
