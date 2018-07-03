#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 17:20:12 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms

from .models import Account


class CreateAuthViewForm(forms.Form):
    user = forms.CharField(
        help_text="Your Biosample User id")

    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text="Your Biosample User password")

    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(CreateAuthViewForm, self).__init__(*args, **kwargs)


class RegisterUserForm(forms.ModelForm):
    user_id = forms.IntegerField(
        widget=forms.HiddenInput)

    name = forms.SlugField(
        help_text="Your Biosample User id")

    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text="Your Biosample User password")

    team = forms.CharField(
        help_text="Your Biosample Team")

    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(RegisterUserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Account
        fields = ('user', 'name', 'password', 'team')
