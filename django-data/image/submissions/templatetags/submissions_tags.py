#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 19 15:48:51 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import template
from image_app.models import Submission

register = template.Library()


@register.simple_tag
def is_waiting(submission):
    waiting = Submission.STATUSES.get_value('waiting')
    if submission.status == waiting:
        return True
    else:
        return False


@register.simple_tag
def has_errors(submission):
    error = Submission.STATUSES.get_value('error')
    if submission.status == error:
        return True
    else:
        return False


@register.simple_tag
def is_ready(submission):
    ready = Submission.STATUSES.get_value('ready')
    if submission.status == ready:
        return True
    else:
        return False
