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

    class Meta:
        model = Sample
        fields = "__all__"
