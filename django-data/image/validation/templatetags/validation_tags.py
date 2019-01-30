#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 10:42:14 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from collections import defaultdict

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def constant_factory(value):
    return lambda: value


@register.filter(name="get_badge")
def get_badge(name):
    # return unknown badge if no validation is done
    if not hasattr(name, 'validationresult'):
        return mark_safe(
            '<span class="badge badge-pill badge-secondary">Unknown'
            '</span></td>'
        )

    # a dictionary to set badges types
    badge_types = defaultdict(constant_factory('danger'))
    badge_types['Pass'] = 'success'
    badge_types['Warning'] = 'warning'

    # get a badge class from status
    status = name.validationresult.status
    badge_class = badge_types[status]

    # get messages
    messages = name.validationresult.result.get_messages()
    messages_str = "<br>".join(messages)

    # set result string
    if status == 'Pass':
        result = (
            '<span class="badge badge-pill badge-{0}"'
            '>{1}</span>'.format(
                badge_class, status)
        )
    else:
        result = (
            '<span class="badge badge-pill badge-{0}" data-toggle="tooltip" '
            'title="{1}" data-html="true" data-placement="right"'
            '>{2}</span>'.format(
                badge_class, messages_str, status)
        )

    # Explicitly mark a string as safe for (HTML) output purposes
    return mark_safe(result)
