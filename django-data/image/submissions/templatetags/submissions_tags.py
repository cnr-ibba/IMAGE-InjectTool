#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 19 15:48:51 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import template
from image_app.models import STATUSES, Submission

register = template.Library()


WAITING = STATUSES.get_value('waiting')
LOADED = STATUSES.get_value('loaded')
ERROR = STATUSES.get_value('error')
READY = STATUSES.get_value('ready')
NEED_REVISION = STATUSES.get_value('need_revision')
SUBMITTED = STATUSES.get_value('submitted')
COMPLETED = STATUSES.get_value('completed')


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


@register.simple_tag
def have_submission(user):
    return Submission.objects.filter(owner=user).exists()
