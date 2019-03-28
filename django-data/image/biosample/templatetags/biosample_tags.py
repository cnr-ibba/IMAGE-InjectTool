#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:16:13 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="get_biosample_link")
def get_biosample_link(biosample_id):
    """A function to get a biosample link from a biosample id"""

    if not biosample_id:
        return None

    link = (
        """<a href="https://wwwdev.ebi.ac.uk/biosamples/samples/"""
        """{0}" target="_blank">{0}""".format(biosample_id))

    # Explicitly mark a string as safe for (HTML) output purposes
    return mark_safe(link)
