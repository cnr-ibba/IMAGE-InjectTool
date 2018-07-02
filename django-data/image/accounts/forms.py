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
    # first name and last name are required fields, even if they arent using
    # django admin add user
    first_name = forms.CharField(
        max_length=254, required=True)

    last_name = forms.CharField(
        max_length=254, required=True)

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

    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')

        super(SignUpForm, self).__init__(*args, **kwargs)


class UserForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=254, required=True)

    last_name = forms.CharField(
        max_length=254, required=True)

    email = forms.CharField(
        max_length=254, required=True, widget=forms.EmailInput())

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class PersonForm(forms.ModelForm):

    class Meta:
        model = Person
        fields = ('initials', 'affiliation', 'role', 'organization')


class MyAccountForm(MultiModelForm):
    form_classes = {
        'user': UserForm,
        'person': PersonForm,
    }

    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')

        super(MyAccountForm, self).__init__(*args, **kwargs)
