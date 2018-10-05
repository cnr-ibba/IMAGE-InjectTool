#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:58:05 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms


# TODO: use ModelForm instead
class ValidateForm(forms.Form):
    submission_id = forms.IntegerField(
        required=True)
