#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 11 16:15:36 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.db import models
from django.db.models import Func, Value

from image_app.models import DictCountry


class Replace(Func):
    function = 'REPLACE'


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

    @classmethod
    def remove_spaces(cls):
        """Annotate objects by removing spaces in word and by returning a
        queryset"""

        # https://docs.djangoproject.com/en/1.11/ref/models/expressions/#func-expressions
        return cls.objects.annotate(
            new_word=Replace('word', Value(" "), Value("")))

    @classmethod
    def check_synonims(cls, words, country):
        """Map words to country language or default one"""

        # get defaul language
        default = DictCountry.objects.get(label="United Kingdom")

        # remove spaces from words
        words = [word.replace(" ", "") for word in words]

        # get synonims in my language. First remove space from qs
        qs = cls.remove_spaces()

        # the filter by provided words
        qs = qs.filter(
            new_word__in=words,
            language__in=[country, default],
            dictspecie__isnull=False)

        # return queryset filtered by word
        return qs.order_by('word').distinct('word')

    @classmethod
    def check_specie_by_synonim(cls, word, country):
        """Test for a word in supplied language or default one"""

        # get defaul language
        default = DictCountry.objects.get(label="United Kingdom")

        # remove space from word
        word = word.replace(" ", "")

        # remove space from qs
        qs = cls.remove_spaces()

        # test if term is defined in supplied language
        if qs.filter(
                new_word=word,
                language=country,
                dictspecie__isnull=False).exists():
            return True

        # test if term is suppliecd in default language
        elif qs.filter(
                new_word=word,
                language=default,
                dictspecie__isnull=False).exists():
            return True

        else:
            # this term is not defined
            return False
