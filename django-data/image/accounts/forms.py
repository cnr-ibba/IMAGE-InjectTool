#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 16:04:02 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

inspired from A Complete Beginner's Guide to Django - Part 4

https://simpleisbetterthancomplex.com/series/2017/09/25/a-complete-beginners-guide-to-django-part-4.html

"""


from django import forms
from django.core import validators
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.text import format_lazy
from django.urls import reverse_lazy

from betterforms.multiform import MultiModelForm
from common.forms import RequestFormMixin
from common.helpers import get_admin_emails
from uid.models import Person


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
        help_text="You have to agree in order to use IMAGE-InjectTool",
        required=True)

    # this will be empty. If a bot tries to fill this, I will raise a
    # forms.ValidationError
    botcatcher = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
        validators=[validators.MaxLengthValidator(0)])

    class Meta:
        model = Person
        fields = ('initials', 'affiliation', 'role')

    def __init__(self, *args, **kwargs):
        super(SignUpPersonForm, self).__init__(*args, **kwargs)

        # The problem might be that the form is defined before the urls have
        # been loaded. So, add label with reverse lazy when class
        # is initialized
        # https://stackoverflow.com/a/7430924
        self.fields['agree_gdpr'].label = mark_safe(
            # In order to evaluate lazy objects in a str.format() like syntax
            # you now have to use format_lazy() instead.
            # https://stackoverflow.com/a/54742333
            format_lazy(
                """I accept IMAGE-InjectTool <a href="{0}" target="_blank">"""
                """terms and conditions</a>""",
                reverse_lazy("terms-and-conditions"),
            )
        )

        self.fields['affiliation'].help_text = mark_safe(
            format_lazy(
                """The institution you belong to. Not listed? please """
                """<a href="mailto:{0}?subject=please add my organization">"""
                """contact us</a>""", get_admin_emails()[0]
            )
        )


class SignUpForm(RequestFormMixin, MultiModelForm):
    form_classes = {
        'user': SignUpUserForm,
        'person': SignUpPersonForm,
    }


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
        fields = ('initials', 'affiliation', 'role')


class MyAccountForm(RequestFormMixin, MultiModelForm):
    form_classes = {
        'user': UserForm,
        'person': PersonForm,
    }
