#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  7 11:54:15 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin

from .models import SpecieSynonym


class SpecieSynonymAdmin(admin.ModelAdmin):
    list_display = ('word', 'dictspecie', 'language')

    list_filter = ('language', 'dictspecie')

    list_select_related = ('language', 'dictspecie')


# Register your models here.
admin.site.register(SpecieSynonym, SpecieSynonymAdmin)
