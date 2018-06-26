#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 16:04:02 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

inspired from A Complete Beginner's Guide to Django - Part 4

https://simpleisbetterthancomplex.com/series/2017/09/25/a-complete-beginners-guide-to-django-part-4.html

"""

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import SignUpPersonForm, PersonForm, SignUpUserForm, UserForm


# Create your views here.
# Using Django creation form
def signup(request):
    if request.method == 'POST':
        # SignUpForm has also passwords
        user_form = SignUpUserForm(request.POST)
        person_form = SignUpPersonForm(request.POST)

        # Two is valid: i need to ensure that both forms are valid
        if user_form.is_valid() and person_form.is_valid():
            # this will save user and default person data
            user = user_form.save()

            # reload person_form using user.person as a instance
            person_form = SignUpPersonForm(request.POST, instance=user.person)

            # then update person data
            person_form.save()

            # Auto connect after registration
            auth_login(request, user)
            return redirect('index')
    else:
        user_form = SignUpUserForm()
        person_form = SignUpPersonForm()

    # pass only a object in context
    form_list = [user_form, person_form]

    return render(request, 'accounts/signup.html', {'form_list': form_list})


@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        person_form = PersonForm(request.POST, instance=request.user.person)

        if user_form.is_valid() and person_form.is_valid():
            user_form.save()
            person_form.save()

            messages.success(
                request,
                message="Your profile was successfully updated!",
                extra_tags="alert alert-dismissible alert-success")

            return redirect('image_app:dashboard')

        else:
            messages.error(
                request,
                message="Please correct the errors below",
                extra_tags="alert alert-dismissible alert-danger")

    # method GET
    else:
        user_form = UserForm(instance=request.user)
        person_form = PersonForm(instance=request.user.person)

        # pass only a object in context
        form_list = [user_form, person_form]

    return render(request, 'accounts/update_user.html', {
        'form_list': form_list
    })
