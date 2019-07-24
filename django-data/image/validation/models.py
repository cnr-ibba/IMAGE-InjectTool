#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 11:09:02 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField

from image_app.models import Name, Animal, Sample, Submission


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
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE)

    all_count = models.PositiveIntegerField(
        default=0,
        help_text="number of all samples or animals in a submission")

    validation_known_count = models.PositiveIntegerField(default=0)

    issues_count = models.PositiveIntegerField(
        default=0,
        help_text="number of samples or animals with issues in validation")

    pass_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)

    # TODO: should this be a ENUM object?
    type = models.CharField(max_length=6, blank=True, null=True)

    messages = ArrayField(
        models.TextField(max_length=255, blank=True),
        default=list
    )

    def get_unknown_count(self):
        """Returns number of samples or animals with unknown validation"""

        return self.all_count - self.validation_known_count

    def reset_all_count(self):
        """Set all_count column according to Animal/Sample objects"""

        if self.type == "animal":
            self.all_count = Animal.objects.filter(
                name__submission=self.submission).count()

        elif self.type == "sample":
            self.all_count = Sample.objects.filter(
                name__submission=self.submission).count()

        else:
            raise Exception("Unknown type '%s'" % (self.type))

        self.save()

    def reset(self):
        """Sets all counts to 0, except all_count field"""
        self.pass_count = 0
        self.warning_count = 0
        self.error_count = 0
        self.issues_count = 0
        self.validation_known_count = 0
        self.messages = list()
        self.save()
