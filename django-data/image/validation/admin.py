#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 29 11:28:48 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin
from django.template.defaultfilters import truncatechars

from .models import ValidationResult, ValidationSummary


class ValidationSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'submission_title', 'owner', 'type', 'all_count',
        'validation_known_count', 'issues_count', 'pass_count',
        'warning_count', 'error_count']

    list_select_related = ('submission', 'submission__owner')

    list_filter = ['submission__owner', 'submission__status']

    def submission_title(self, obj):
        return obj.submission.title

    def owner(self, obj):
        return obj.submission.owner


class ValidationResultAdmin(admin.ModelAdmin):
    list_display = [
        'submission_title', 'owner', 'content_type', 'object_id', 'status',
        'short_messages']

    list_select_related = ('submission', 'submission__owner', 'content_type')

    list_per_page = 20

    list_filter = ['submission__owner', 'status']

    def submission_title(self, obj):
        return obj.submission.title

    def owner(self, obj):
        return obj.submission.owner

    def short_messages(self, obj):
        return truncatechars(",".join(obj.messages), 60)


# Register your models here.
admin.site.register(ValidationResult, ValidationResultAdmin)
admin.site.register(ValidationSummary, ValidationSummaryAdmin)
