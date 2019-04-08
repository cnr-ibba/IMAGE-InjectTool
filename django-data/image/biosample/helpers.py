#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 12:13:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import re

from decouple import AutoConfig

from pyUSIrest.auth import Auth

from django.conf import settings


# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)

# a pattern to correctly parse aliases
ALIAS_PATTERN = re.compile(r"IMAGE([AS])([0-9]+)")


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


def parse_image_alias(alias):
    """Parse alias and return table and pk"""

    match = re.search(ALIAS_PATTERN, alias)

    letter, padded_pk = match.groups()
    table, pk = None, None

    if letter == "A":
        table = "Animal"

    elif letter == "S":
        table = "Sample"

    pk = int(padded_pk)

    return table, pk
