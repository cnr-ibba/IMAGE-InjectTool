#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 15:38:46 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms

from image_app.models import Animal, Name, DictBreed
from common.forms import RequestFormMixin


class UpdateAnimalForm(RequestFormMixin, forms.ModelForm):
    # disabling via class attributes. None mean the default queryset. This
    # queryset will be overwrite by __init__ in order to display only names
    # belonging to this submission in dropdown list.
    # name = forms.ModelChoiceField(
    #     None,
    #     required=False,
    #     widget=forms.Select(attrs={'disabled': True})
    # )

    class Meta:
        model = Animal
        fields = (
            'name',
            'alternative_id',
            'description',
            'breed',
            'sex',
            'father',
            'mother',
            'birth_location',
            'birth_location_latitude',
            'birth_location_longitude',
            'birth_location_accuracy'
        )

        # HINT: the readonly attribute is not valid in HTML5 for <select>
        # (MultipleChoice field) need to be disabled.
        # https://stackoverflow.com/questions/368813/html-form-readonly-select-tag-input
        widgets = {
            'name': forms.Select(attrs={'disabled': True}),
            'mother': forms.Select(attrs={'disabled': True}),
            'father': forms.Select(attrs={'disabled': True}),
        }

    def __init__(self, animal, *args, **kwargs):
        # call base methods (and RequestFormMixin.__init__)
        super(UpdateAnimalForm, self).__init__(*args, **kwargs)

        # get only names belonging to current submission
        my_names = Name.objects.filter(
            submission=animal.submission, owner=self.request.user)

        # override name queryset and other attributes
        # BUG: forcing those fields as not required validate the form, but
        # the update query will use NULL values in not null database field
        # and make query fail
        self.fields['name'].queryset = Name.objects.filter(pk=animal.name.pk)
        self.fields['name'].required = False

        self.fields['father'].queryset = my_names
        self.fields['father'].required = False

        self.fields['mother'].queryset = my_names
        self.fields['mother'].required = False

        # filter breed by country and specie
        self.fields['breed'].queryset = DictBreed.objects.select_related(
            'specie', 'country').filter(
                country=animal.submission.gene_bank_country,
                specie=animal.specie)
