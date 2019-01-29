#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 29 11:28:48 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin

from .models import ValidationResult


class ValidationResultAdmin(admin.ModelAdmin):
    list_select_related = ('name', )

    list_per_page = 20


# Register your models here.
admin.site.register(ValidationResult, ValidationResultAdmin)
