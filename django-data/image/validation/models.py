#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 11:09:02 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField

from image_app.models import Name


class ValidationResult(models.Model):
    name = models.OneToOneField(
        Name,
        on_delete=models.CASCADE)

    status = models.CharField(
            max_length=255,
            blank=False,
            null=True)

    messages = ArrayField(
        models.CharField(max_length=255, blank=True),
        default=list
    )

    def __str__(self):
        return "%s:%s" % (self.name, self.status)
