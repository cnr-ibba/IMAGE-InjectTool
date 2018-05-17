#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 11 14:52:46 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import subprocess

from django import template

register = template.Library()


# A free interpretation of https://stackoverflow.com/a/23584696
@register.simple_tag
def git_describe():
    # https://stackoverflow.com/a/14989911
    return subprocess.check_output(["git", "describe", "--always"]).strip()


# form fields
@register.filter
def field_type(bound_field):
    return bound_field.field.widget.__class__.__name__


@register.filter
def input_class(bound_field):
    css_class = ''
    if bound_field.form.is_bound:
        if bound_field.errors:
            css_class = 'is-invalid'
        # let’s just ignore the is-valid and is-invalid CSS classes in some
        # cases.
        elif field_type(bound_field) != 'PasswordInput':
            css_class = 'is-valid'
    return 'form-control {}'.format(css_class)
