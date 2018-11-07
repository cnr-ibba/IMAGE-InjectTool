#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 11 16:15:36 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.db import models


# Create your models here.
class SpecieSynonim(models.Model):
    # linking to others modules
    dictspecie = models.ForeignKey(
        'image_app.DictSpecie',
        on_delete=models.CASCADE,
        null=True)

    language = models.ForeignKey(
        'image_app.DictCountry',
        on_delete=models.CASCADE)

    word = models.CharField(
        max_length=255,
        blank=False)

    class Meta:
        # db_table will be <app_name>_<classname>
        unique_together = (("dictspecie", "language", "word"),)

    def __str__(self):
        return "{language}:{word} ({dictspecie})".format(
            language=self.language.label,
            word=self.word,
            dictspecie=self.dictspecie)
