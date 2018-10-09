#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 19 15:48:51 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import template
from image_app.models import Submission

register = template.Library()


WAITING = Submission.STATUSES.get_value('waiting')
LOADED = Submission.STATUSES.get_value('loaded')
ERROR = Submission.STATUSES.get_value('error')
READY = Submission.STATUSES.get_value('ready')
NEED_REVISION = Submission.STATUSES.get_value('need_revision')
SUBMITTED = Submission.STATUSES.get_value('submitted')
COMPLETED = Submission.STATUSES.get_value('completed')


@register.simple_tag
def can_edit(submission):
    if submission.status not in [WAITING, SUBMITTED]:
        return True

    else:
        return False


@register.simple_tag
def can_validate(submission):
    if submission.status not in [ERROR, WAITING, SUBMITTED, COMPLETED]:
        return True
    else:
        return False


@register.simple_tag
def can_submit(submission):
    if submission.status == READY:
        return True
    else:
        return False
