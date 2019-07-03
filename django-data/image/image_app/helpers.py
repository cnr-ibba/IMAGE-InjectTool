#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 12:41:05 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Common functions in image_app

"""

import re

from .models import Animal, Sample

# a pattern to correctly parse aliases
ALIAS_PATTERN = re.compile(r"IMAGE([AS])([0-9]+)")


def parse_image_alias(alias):
    """Parse alias and return table and pk"""

    match = re.search(ALIAS_PATTERN, alias)

    if not match:
        raise Exception("Cannot deal with '%s'" % (alias))

    letter, padded_pk = match.groups()
    table, pk = None, None

    if letter == "A":
        table = "Animal"

    elif letter == "S":
        table = "Sample"

    pk = int(padded_pk)

    return table, pk


def get_model_object(table, pk):
    """Get a model object relying on table name (Sample/Alias) and pk"""

    # get sample object
    if table == "Animal":
        sample_obj = Animal.objects.get(pk=pk)

    elif table == "Sample":
        sample_obj = Sample.objects.get(pk=pk)

    else:
        raise Exception("Unknown table '%s'" % (table))

    return sample_obj
