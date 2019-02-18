#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 15:38:46 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms

from image_app.models import Sample
from common.forms import RequestFormMixin


class UpdateSampleForm(RequestFormMixin, forms.ModelForm):
    disabled_name = forms.CharField(disabled=True, label="Name")
    disabled_animal = forms.CharField(disabled=True, label="Animal")

    class Meta:
        model = Sample
        fields = (
            'disabled_name',
            'alternative_id',
            'description',
            'disabled_animal',
            'protocol',
            'collection_date',
            'collection_place_latitude',
            'collection_place_longitude',
            'collection_place',
            'collection_place_accuracy',
            'organism_part',
            'developmental_stage',
            'physiological_stage',
            'animal_age_at_collection',
            'availability',
            'storage',
            'storage_processing',
            'preparation_interval'
        )

    def __init__(self, sample, *args, **kwargs):
        # call base methods (and RequestFormMixin.__init__)
        super(UpdateSampleForm, self).__init__(*args, **kwargs)
