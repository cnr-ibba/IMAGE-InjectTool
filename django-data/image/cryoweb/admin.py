#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 28 13:02:55 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin

from .models import VBreedsSpecies, VTransfer, VAnimal, VVessels

# Register your models here.
admin.site.register(VBreedsSpecies)
admin.site.register(VTransfer)
admin.site.register(VAnimal)
admin.site.register(VVessels)
