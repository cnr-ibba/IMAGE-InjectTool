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
