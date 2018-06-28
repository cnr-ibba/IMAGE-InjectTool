#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 16:04:02 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

inspired from A Complete Beginner's Guide to Django - Part 4

https://simpleisbetterthancomplex.com/series/2017/09/25/a-complete-beginners-guide-to-django-part-4.html

"""


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from betterforms.multiform import MultiModelForm

from image_app.models import Person


class SignUpUserForm(UserCreationForm):
    email = forms.CharField(
        max_length=254, required=True, widget=forms.EmailInput())

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'password1',
            'password2')


class SignUpPersonForm(forms.ModelForm):
    # custom attributes
    agree_gdpr = forms.BooleanField(
        label="I accept IMAGE-InjectTool terms and conditions",
        help_text="You have to agree in order to use IMAGE-InjectTool")

    class Meta:
        model = Person
        fields = ('initials', 'affiliation', 'role', 'organization')


class SignUpForm(MultiModelForm):
    form_classes = {
        'user': SignUpUserForm,
        'person': SignUpPersonForm,
    }


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class PersonForm(forms.ModelForm):

    class Meta:
        model = Person
        fields = ('initials', 'affiliation', 'role', 'organization')
