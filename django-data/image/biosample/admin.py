# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 11:39:15 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin

from .models import (
    Account, ManagedTeam, Submission, SubmissionData)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'uid_submission', 'usi_submission_id', 'created_at', 'updated_at',
        'status'
    )

    # I cannot edit a auto_add_now field
    readonly_fields = ('created_at', 'updated_at')


class SubmissionDataAdmin(admin.ModelAdmin):
    list_display = (
        'submission', 'content_type', 'object_id', 'status'
    )


# --- registering applications


# Register your models here.
admin.site.register(Account)
admin.site.register(ManagedTeam)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(SubmissionData, SubmissionDataAdmin)
