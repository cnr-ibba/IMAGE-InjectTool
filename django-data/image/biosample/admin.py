# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 11:39:15 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin

from .models import (
    Account, ManagedTeam, Submission, SubmissionData, OrphanSample)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'uid_submission', 'usi_submission_name', 'created_at', 'updated_at',
        'message', 'status'
    )

    # I cannot edit a auto_add_now field
    readonly_fields = ('created_at', 'updated_at')

    list_filter = ('uid_submission__owner', 'status')

    list_per_page = 15


class SubmissionDataAdmin(admin.ModelAdmin):
    list_display = (
        'submission', 'content_type', 'object_id'
    )

    list_filter = (
        'submission__uid_submission__owner',
        'submission__uid_submission__status')

    list_per_page = 15


class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'name', 'team'
    )

    list_per_page = 15


class OrphanSampleAdmin(admin.ModelAdmin):
    list_display = (
        'biosample_id', 'found_at', 'ignore', 'name', 'removed', 'removed_at'
    )

    # I cannot edit a auto_add_now field
    readonly_fields = ('found_at', 'removed_at')

    list_per_page = 15


# --- registering applications


# Register your models here.
admin.site.register(Account, AccountAdmin)
admin.site.register(ManagedTeam)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(SubmissionData, SubmissionDataAdmin)
admin.site.register(OrphanSample, OrphanSampleAdmin)
