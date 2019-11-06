#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 15:34:05 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="child_of")
def child_of(animal):
    """A function to get information on animal parents"""

    parents = []

    # get father relationship
    if animal.father:
        father = animal.father

        link = '<a href="{url}">{name}</a>'.format(
            url=father.get_absolute_url(),
            name=father.name)

        parents.append(link)

    # get mother relationship
    if animal.mother:
        mother = animal.mother

        link = '<a href="{url}">{name}</a>'.format(
            url=mother.get_absolute_url(),
            name=mother.name)

        parents.append(link)

    # Explicitly mark a string as safe for (HTML) output purposes
    return mark_safe(", ".join(parents))
