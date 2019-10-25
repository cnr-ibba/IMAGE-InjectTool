#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:16:13 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import template
from django.utils.safestring import mark_safe

from common.constants import (
    BIOSAMPLE_URL, EBI_AAP_API_AUTH, BIOSAMPLE_API_ROOT)

register = template.Library()


@register.filter(name="get_biosample_link")
def get_biosample_link(biosample_id):
    """A function to get a biosample link from a biosample id"""

    if not biosample_id:
        return None

    link = (
        """<a href="{0}/{1}" target="_blank">{1}""".format(
                BIOSAMPLE_URL, biosample_id))

    # Explicitly mark a string as safe for (HTML) output purposes
    return mark_safe(link)


@register.simple_tag(name="is_biosample_test_env")
def is_biosample_test_env():
    """A function to assert if I'm using biosample production environment
    or not"""

    if (BIOSAMPLE_URL == "https://wwwdev.ebi.ac.uk/biosamples/samples" and
            EBI_AAP_API_AUTH == "https://explore.api.aai.ebi.ac.uk/auth" and
            BIOSAMPLE_API_ROOT == "https://submission-test.ebi.ac.uk/api/"):
        return True

    else:
        return False
