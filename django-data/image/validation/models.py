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
        models.TextField(max_length=255, blank=True),
        default=list
    )

    def __str__(self):
        return "%s:%s" % (self.name, self.status)


class ValidationSummary(models.Model):
    submission = models.ForeignKey('image_app.Submission',
                                   on_delete=models.CASCADE)

    all_count = models.PositiveIntegerField(default=0)
    pass_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    json_count = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=6, blank=True, null=True)
    messages = ArrayField(
        models.TextField(max_length=255, blank=True),
        default=list
    )

    # Returns number of all samples or animals in submission
    def get_all_count(self):
        return self.all_count

    # Returns number of samples or animals with unknown validation
    def get_unknown_count(self):
        return self.all_count - (self.pass_count + self.warning_count +
                                 self.error_count + self.json_count)

    # Returns number of samples or animals with issues in validation
    def get_issues_count(self):
        return self.error_count + self.json_count
