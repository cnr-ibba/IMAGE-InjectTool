#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 11:09:02 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from uid.models import Animal, Sample, Submission


class ValidationResult(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE)

    # limit choices for contenttypes
    # https://axiacore.com/blog/how-use-genericforeignkey-django-531/
    name_limit = models.Q(app_label='uid', model='animal') | \
        models.Q(app_label='uid', model='sample')

    # Below the mandatory fields for generic relation
    # https://simpleisbetterthancomplex.com/tutorial/2016/10/13/how-to-use-generic-relations.html
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=name_limit)

    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    status = models.CharField(
            max_length=255,
            blank=False,
            null=True)

    messages = ArrayField(
        models.TextField(max_length=255, blank=True),
        default=list,
        blank=True
    )

    class Meta:
        unique_together = ('content_type', 'object_id')

    def __str__(self):
        return "(%s - %s:%s) %s" % (
            self.submission,
            self.content_type,
            self.object_id,
            self.status)


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

    # HINT: even if it's like a ENUM object, changing this at this moment means
    # changing a lot of things. This will remain a char field, for the moment
    type = models.CharField(max_length=6, blank=True, null=True)

    messages = ArrayField(
        JSONField(default=dict),
        default=list
    )

    class Meta:
        unique_together = (("submission", "type"),)
        verbose_name_plural = "validation summaries"

    def __str__(self):
        return "Summary for %s, type: %s, all:%s, pass:%s" % (
            self.submission,
            self.type,
            self.all_count,
            self.pass_count)

    def get_unknown_count(self):
        """Returns number of samples or animals with unknown validation"""

        return self.all_count - self.validation_known_count

    def reset_all_count(self):
        """Set all_count column according to Animal/Sample objects"""

        if self.type == "animal":
            self.all_count = Animal.objects.filter(
                submission=self.submission).count()

        elif self.type == "sample":
            self.all_count = Sample.objects.filter(
                submission=self.submission).count()

        else:
            raise Exception("Unknown type '%s'" % (self.type))

        self.save()

    def reset(self):
        """Sets all counts and other counters to 0"""

        self.pass_count = 0
        self.warning_count = 0
        self.error_count = 0
        self.issues_count = 0
        self.validation_known_count = 0
        self.messages = list()
        self.save()

        # reset also all counts
        self.reset_all_count()
