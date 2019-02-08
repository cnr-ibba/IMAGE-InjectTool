#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 15:38:46 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms

from image_app.models import Animal, DictBreed
from common.forms import RequestFormMixin


class UpdateAnimalForm(RequestFormMixin, forms.ModelForm):
    disabled_name = forms.CharField(disabled=True, label="Name")
    disabled_mother = forms.CharField(disabled=True, label="Mother")
    disabled_father = forms.CharField(disabled=True, label="Father")

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
