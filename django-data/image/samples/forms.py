#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 15:38:46 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms

from image_app.models import Sample
from common.forms import RequestFormMixin
from common.constants import MISSING


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
            'collection_place',
            'collection_place_latitude',
            'collection_place_longitude',
            'collection_place_accuracy',
            'organism_part',
            'developmental_stage',
            'physiological_stage',
            'animal_age_at_collection',
            'animal_age_at_collection_units',
            'availability',
            'storage',
            'storage_processing',
            'preparation_interval'
        )

    def __init__(self, sample, *args, **kwargs):
        # call base methods (and RequestFormMixin.__init__)
        super(UpdateSampleForm, self).__init__(*args, **kwargs)

    def clean(self):
        # get my data
        cleaned_data = super(UpdateSampleForm, self).clean()
        collection_place = cleaned_data.get("collection_place")
        accuracy = cleaned_data.get("collection_place_accuracy")

        if collection_place and accuracy == MISSING:
            # HINT: can I have precise accuracy with no coordinate?
            # TODO: what will happen with bulk update? need to implement
            # the same validator
            msg = ("You can't have missing geographic information with a "
                   "collection place")
            self.add_error('collection_place_accuracy', msg)

            # raising an exception:
            raise forms.ValidationError(msg, code='invalid')
