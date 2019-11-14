#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 12:56:25 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

from django import forms

from common.forms import RequestFormMixin

from .models import Organization


class OrganizationForm(RequestFormMixin, forms.ModelForm):
    name = forms.CharField(disabled=True)

    class Meta:
        model = Organization
        fields = '__all__'
