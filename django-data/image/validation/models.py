#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 11:09:02 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import pickle

from django.db import models

from image_app.models import Name


class ValidationResult(models.Model):
    name = models.OneToOneField(
        Name,
        on_delete=models.CASCADE)

    status = models.CharField(
            max_length=255,
            blank=False,
            null=True)

    data = models.BinaryField(
        null=True)

    # a method to dial with image validationtool objects
    @property
    def result(self):
        if self.data is None:
            return None

        return pickle.loads(self.data)

    @result.setter
    def result(self, result):
        self.data = pickle.dumps(result)

        if isinstance(result, list):
            self.status = "Wrong JSON structure"

        else:
            # assign status
            self.status = result.get_overall_status()

    def __str__(self):
        if self.data is None:
            return "No data for %s" % (self.name)

        return "%s for %s" % (self.status, self.name)
