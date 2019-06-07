#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 15:34:05 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import template

register = template.Library()


@register.filter(name="child_of")
def child_of(animal):
    """A function to get information on animal parents"""

    parents = []

    # get father relathionship
    relationship = animal.get_father_relationship()

    if relationship:
        if 'alias' in relationship:
            parents.append(relationship['alias'])

        if 'accession' in relationship:
            parents.append(relationship['accession'])

    # get mother relationship
    relationship = animal.get_mother_relationship()

    if relationship:
        if 'alias' in relationship:
            parents.append(relationship['alias'])

        if 'accession' in relationship:
            parents.append(relationship['accession'])

    return ", ".join(parents)
