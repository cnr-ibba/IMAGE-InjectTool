#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:51:05 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import magic

from django import forms

from image_app.models import Submission
from common.forms import RequestFormMixin


class SubmissionFormMixin():
    def clean(self):
        # I can call this method without providing a 'uploaded file'
        # (for instance, when omitting uploaded file)
        if "uploaded_file" in self.cleaned_data:
            self.check_file_encoding()

    def check_file_encoding(self):
        uploaded_file = self.cleaned_data['uploaded_file']

        # read one chunk of such file
        chunk = next(uploaded_file.chunks())
        magic_line = magic.from_buffer(chunk)
        file_type = magic_line.split(",")[0]

        if "UTF-8" not in file_type:
            # create message and add error
            msg = "Error: file not in UTF-8 format: format was %s" % file_type

            # raising an exception:
            raise forms.ValidationError(msg, code='invalid')


class SubmissionForm(SubmissionFormMixin, RequestFormMixin, forms.ModelForm):
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

        help_texts = {
            'uploaded_file': 'Need to be in UTF-8 format',
        }


# I use forms.Form since I need to pass primary key as a field,
# and I can't use it with a modelform
class ReloadForm(SubmissionFormMixin, RequestFormMixin, forms.ModelForm):
    # custom attributes
    agree_reload = forms.BooleanField(
        label="That's fine. Replace my submission data with this file",
        help_text="You have to check this box to reload your data")

    class Meta:
        model = Submission
        fields = ('uploaded_file',)

        help_texts = {
            'uploaded_file': 'Need to be in UTF-8 format',
        }
