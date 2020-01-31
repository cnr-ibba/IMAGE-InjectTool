#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:51:05 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import magic
import tempfile

from django import forms
from django.conf import settings

from common.constants import CRB_ANIM_TYPE, TEMPLATE_TYPE
from common.forms import RequestFormMixin
from common.helpers import get_admin_emails
from uid.models import Submission
from crbanim.helpers import CRBAnimReader
from excel.helpers import ExcelTemplateReader


class SubmissionFormMixin():
    def clean(self):
        # test if I have a submission with the provided data
        self.check_submission_exists()

        # I can call this method without providing a 'uploaded file'
        # (for instance, when omitting uploaded file)
        if "uploaded_file" in self.cleaned_data:
            # avoid file type for excel types (is not an text file)
            if ("datasource_type" in self.cleaned_data and
                    self.cleaned_data["datasource_type"] != TEMPLATE_TYPE):
                self.check_file_encoding()

            # check crbanim files only if provided
            if ("datasource_type" in self.cleaned_data and
                    self.cleaned_data["datasource_type"] == CRB_ANIM_TYPE):
                self.check_crbanim_columns()

            # check template files only if provided
            if ("datasource_type" in self.cleaned_data and
                    self.cleaned_data["datasource_type"] == TEMPLATE_TYPE):
                self.check_template_file()

    def check_submission_exists(self):
        """Test if I already have a submission with the same data"""

        # get unique attributes
        unique_together = Submission._meta.unique_together[0]

        # get submitted attributes
        data = {key: self.cleaned_data.get(key) for key in unique_together}

        # ovverride owner attribute
        data['owner'] = self.request.user

        # test for a submission object with the same attributes
        if Submission.objects.filter(**data).exists():
            msg = (
                "Error: There is already a submission with the same "
                "attributes. Please change one of the following: "
                "Gene bank name, Gene bank country, Data source type and "
                "Data source version")

            # raising an exception:
            raise forms.ValidationError(msg, code='invalid')

    def check_file_encoding(self):
        uploaded_file = self.cleaned_data['uploaded_file']

        # read one chunk of such file
        chunk = next(uploaded_file.chunks())
        magic_line = magic.from_buffer(chunk)
        file_type = magic_line.split(",")[0]

        if "UTF-8" not in file_type and "ASCII" not in file_type:
            # create message and add error
            msg = (
                "Error: file not in UTF-8 nor ASCII format: "
                "format was %s" % file_type)

            # raising an exception:
            raise forms.ValidationError(msg, code='invalid')

    def check_crbanim_columns(self):
        """Check if a CRBanim file has mandatory columns"""

        uploaded_file = self.cleaned_data['uploaded_file']

        # read one chunk of such file
        chunk = next(uploaded_file.chunks())

        # now determine if CRBanim file is valid. chunk is in binary format
        # neet to convert to a string, fortunately I've already check that
        # file is in UTF-8
        check, not_found = CRBAnimReader.is_valid(chunk.decode("utf-8"))

        if check is False:
            msg = "Error: file lacks of CRBanim mandatory columns: %s" % (
                not_found)

            # raising an exception:
            raise forms.ValidationError(msg, code='invalid')

    def check_template_file(self):
        """Check if template file has columns and sheets"""

        uploaded_file = self.cleaned_data['uploaded_file']

        chunk = next(uploaded_file.chunks())
        magic_line = magic.from_buffer(chunk)

        if 'Microsoft' not in magic_line:
            msg = "The file you provided is not a Template file"
            raise forms.ValidationError(msg, code='invalid')

        # xlrd can manage only files. Write a temporary file
        with tempfile.NamedTemporaryFile(delete=True) as tmpfile:
            for chunk in uploaded_file.chunks():
                tmpfile.write(chunk)

            # open the file with proper model
            reader = ExcelTemplateReader()
            reader.read_file(tmpfile.name)

            # check that template has at least breed, animal, sample sheets
            check, not_found = reader.check_sheets()

            if check is False:
                msg = "Error: file lacks of Template mandatory sheets: %s" % (
                    not_found)

                # raising an exception:
                raise forms.ValidationError(msg, code='invalid')

            # check that template has at least breed, animal, sample sheets
            check, not_found = reader.check_columns()

            if check is False:
                msg = "Error: file lacks of Template mandatory columns: %s" % (
                    not_found)

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
            'uploaded_file': 'Need to be in UTF-8 or ASCII format',
            'organization': (
                """Who owns the data. Not listed? please """
                """<a href="mailto:{0}?subject=please add my organization">"""
                """contact us</a>""".format(get_admin_emails()[0])
            ),
            'datasource_type': (
                """example: CryoWeb. Need an empty template file? """
                """download it from <a href="%s%s">here</a>""" % (
                    settings.MEDIA_URL,
                    "Image_sample_empty_template_20191002.xlsx")
            )
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
        fields = (
            'datasource_type',
            'datasource_version',
            'uploaded_file',
        )

        help_texts = {
            'uploaded_file': 'Need to be in UTF-8 or ASCII format',
            'datasource_type': (
                """example: CryoWeb. Need an empty template file? """
                """download it from <a href="%s%s">here</a>""" % (
                    settings.MEDIA_URL,
                    "Image_sample_empty_template_20191002.xlsx")
            )
        }


class UpdateSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = (
            'title',
            'description',
            'gene_bank_name',
            'gene_bank_country',
            'organization',
        )

        help_texts = {
            'organization': (
                """Who owns the data. Not listed? please """
                """<a href="mailto:{0}?subject=please add my organization">"""
                """contact us</a>""".format(get_admin_emails()[0])
            )
        }
