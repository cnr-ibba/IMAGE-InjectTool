#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 15:38:46 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms

from uid.models import Animal, DictBreed
from common.forms import RequestFormMixin
from common.constants import MISSING


class UpdateAnimalForm(RequestFormMixin, forms.ModelForm):
    disabled_name = forms.CharField(
        disabled=True,
        label="Name")
    disabled_mother = forms.CharField(
        disabled=True,
        label="Mother",
        required=False)
    disabled_father = forms.CharField(
        disabled=True,
        label="Father",
        required=False)

    class Meta:
        model = Animal
        fields = (
            'disabled_name',
            'alternative_id',
            'description',
            'breed',
            'sex',
            'disabled_mother',
            'disabled_father',
            'birth_date',
            'birth_location',
            'birth_location_latitude',
            'birth_location_longitude',
            'birth_location_accuracy'
        )

    def __init__(self, animal, *args, **kwargs):
        # call base methods (and RequestFormMixin.__init__)
        super(UpdateAnimalForm, self).__init__(*args, **kwargs)

        # filter breed by country and specie
        self.fields['breed'].queryset = DictBreed.objects.select_related(
            'specie', 'country').filter(
                country=animal.submission.gene_bank_country,
                specie=animal.specie)

        self.fields['breed'].label = "Supplied Breed"

    def clean(self):
        # get my data
        cleaned_data = super(UpdateAnimalForm, self).clean()
        birth_location = cleaned_data.get("birth_location")
        accuracy = cleaned_data.get("birth_location_accuracy")

        if birth_location and accuracy == MISSING:
            # HINT: can I have precise accuracy with no coordinate?
            # TODO: what will happen with bulk update? need to implement
            # the same validator
            msg = ("You can't have missing geographic information with a "
                   "birth location")
            self.add_error('birth_location_accuracy', msg)

            # raising an exception:
            raise forms.ValidationError(msg, code='invalid')
