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
