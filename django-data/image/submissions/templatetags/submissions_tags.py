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
def can_edit(submission):
    return submission.can_edit()


@register.simple_tag
def can_validate(submission):
    return submission.can_validate()


@register.simple_tag
def can_submit(submission):
    return submission.can_submit()


@register.simple_tag
def have_submission(user):
    return Submission.objects.filter(owner=user).exists()
