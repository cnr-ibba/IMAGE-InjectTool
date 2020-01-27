# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 11:39:15 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin
from django.template.defaultfilters import truncatechars

from .models import (
    Account, ManagedTeam, Submission, SubmissionData, OrphanSample)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'submission_title', 'usi_submission_name', 'created_at', 'updated_at',
        'status', 'samples_count', 'samples_status', 'short_message',
    )

    list_select_related = ('uid_submission',)

    def short_message(self, obj):
        return truncatechars(obj.message, 40)

    # rename column in admin
    short_message.short_description = "Message"

    def submission_title(self, obj):
        return obj.uid_submission.title

    list_filter = ('uid_submission__owner', 'status')

    list_per_page = 15

    # I cannot edit a auto_add_now field
    readonly_fields = ('uid_submission', 'created_at', 'updated_at')

    fields = (
        'uid_submission', 'usi_submission_name', 'created_at', 'updated_at',
        'message', 'status', 'samples_count', 'samples_status'
    )


class SubmissionDataAdmin(admin.ModelAdmin):
    list_display = (
        'short_submission', 'submission_title', 'status', 'content_type',
        'object_id'
    )

    def short_submission(self, obj):
        return obj.submission.usi_submission_name

    # rename column in admin
    short_submission.short_description = "USI Submission"

    # rename column in admin
    short_submission.short_description = "USI Submission"

    def status(self, obj):
        return obj.submission.get_status_display()

    def submission_title(self, obj):
        return obj.submission.uid_submission.title

    list_filter = (
        'submission__uid_submission__owner',
        'submission__uid_submission__status')

    list_per_page = 15

    # Fields I don't want to edit
    readonly_fields = ('submission',)

    fields = (
        'submission', 'content_type',
        'object_id'
    )


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
