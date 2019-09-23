#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 28 13:02:55 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin

from .models import VAnimal, VBreedsSpecies, VTransfer, VVessels


class VBreedsSpeciesAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = (
        'breed_id', 'ext_breed', 'ext_species', 'efabis_mcname',
        'efabis_species', 'efabis_country')
    list_filter = ('ext_breed', 'ext_species')


class VAnimalAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = (
        'db_animal', 'ext_animal', 'ext_sire', 'ext_dam', 'ext_sex',
        'ext_breed', 'ext_species', 'comment')
    list_filter = ('ext_breed', 'ext_species')


class VVesselsAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = (
        'db_vessel', 'ext_vessel', 'ext_animal', 'ext_protocol_id',
        'ext_vessel_type')


# Register your models here.
admin.site.register(VBreedsSpecies, VBreedsSpeciesAdmin)
admin.site.register(VTransfer)
admin.site.register(VAnimal, VAnimalAdmin)
admin.site.register(VVessels, VVesselsAdmin)
