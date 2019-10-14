#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 29 11:28:48 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin

from .models import ValidationResult, ValidationSummary


class ValidationSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'submission', 'type', 'all_count', 'validation_known_count',
        'issues_count', 'pass_count', 'warning_count', 'error_count']

    list_filter = ['submission', ]

    list_select_related = ('submission', 'submission__gene_bank_country')


class ValidationResultAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'messages']

    list_filter = ['name__submission', 'status']

    list_select_related = ('name', 'name__submission')

    list_per_page = 20


# Register your models here.
admin.site.register(ValidationResult, ValidationResultAdmin)
admin.site.register(ValidationSummary, ValidationSummaryAdmin)
