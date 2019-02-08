#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:51:05 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms

from image_app.models import Submission
from common.forms import RequestFormMixin


class SubmissionForm(RequestFormMixin, forms.ModelForm):
    class Meta:
        model = Submission
        fields = (
            'title',
            'description',
            'gene_bank_name',
            'gene_bank_country',
            'organization',
            'datasource_type',
            'datasource_version',
            'uploaded_file'
        )


# I use forms.Form since I need to pass primary key as a field,
# and I can't use it with a modelform
class ReloadForm(forms.ModelForm):
    # custom attributes
    agree_reload = forms.BooleanField(
        label="That's fine. Replace my submission data with this file",
        help_text="You have to check this box to reload your data")

    class Meta:
        model = Submission
        fields = ('uploaded_file',)
