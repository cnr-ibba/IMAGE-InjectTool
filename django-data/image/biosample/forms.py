#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 17:20:12 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django import forms
from django.contrib.auth import password_validation

from .models import Account


class CreateAuthViewForm(forms.Form):
    user = forms.CharField(
        help_text="Your Biosample User id",
        disabled=True)

    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text="Your Biosample User password")

    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(CreateAuthViewForm, self).__init__(*args, **kwargs)


class RegisterUserForm(forms.ModelForm):
    name = forms.SlugField(
        help_text="Your Biosample User id")

    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text="Your Biosample User password")

    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(RegisterUserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Account
        fields = ('name', 'team')


class CreateUserForm(forms.Form):
    """Based on django.contrib.ath.form"""

    error_messages = {
        'password_mismatch': "The two password fields didn't match."
    }

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Enter the same password as before, for verification.",
    )

    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')

        if 'username' in kwargs:
            self.username = kwargs.pop('username')

        super(CreateUserForm, self).__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        try:
            password_validation.validate_password(password2)

        except forms.ValidationError as error:
            self.add_error('password2', error)

        return password2
