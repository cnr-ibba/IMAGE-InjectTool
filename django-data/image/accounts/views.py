#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 16:04:02 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

inspired from A Complete Beginner's Guide to Django - Part 4

https://simpleisbetterthancomplex.com/series/2017/09/25/a-complete-beginners-guide-to-django-part-4.html

"""

from django.contrib import messages
from django.contrib.auth import login as auth_login, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy

from .forms import SignUpForm, MyAccountForm


class SignUpView(CreateView):
    # import a multiform object
    form_class = SignUpForm
    success_url = reverse_lazy('index')
    template_name = 'accounts/signup.html'

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    def get_form_kwargs(self):
        kwargs = super(SignUpView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # Save the user first, because the profile needs a user before it
        # can be saved. When I save user, I save also person since is related
        # to user
        user = form['user'].save()

        # I re-initialize the form with user.username (from database)
        # maybe I can use get_or_create to get a person object then update it
        form = SignUpForm(
            self.request.POST,
            instance={
                'user': user,
                'person': user.person,
            }
        )
        form.save()

        # Auto connect after registration
        auth_login(self.request, user)

        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(
            self.request,
            message="Please correct the errors below",
            extra_tags="alert alert-dismissible alert-danger")

        return super(SignUpView, self).form_invalid(form)


# I need a model instance to work with UpdateView
User = get_user_model()


# dispatch is an internal method Django use (defined inside the View class)
# transaction atomic allows us to create a block of code within which the
# atomicity on the database is guaranteedIf the block of code is successfully
# completed, the changes are committed to the database
@method_decorator(login_required, name='dispatch')
class MyAccountView(UpdateView):
    # applying user model (that has relation with person model)
    model = User
    # import a multiform object
    form_class = MyAccountForm
    success_url = reverse_lazy('image_app:dashboard')
    template_name = 'accounts/update_user.html'

    def get_object(self):
        return self.request.user

    # https://django-betterforms.readthedocs.io/en/latest/multiform.html#working-with-updateview
    def get_form_kwargs(self):
        kwargs = super(MyAccountView, self).get_form_kwargs()
        kwargs.update(instance={
            'user': self.object,
            'person': self.object.person,
        })

        # add the request to the kwargs
        # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
        kwargs['request'] = self.request
        return kwargs

    def form_invalid(self, form):
        messages.error(
            self.request,
            message="Please correct the errors below",
            extra_tags="alert alert-dismissible alert-danger")

        return super(MyAccountView, self).form_invalid(form)

    def get_success_url(self):
        """Override default function"""

        messages.success(
            self.request,
            message="Your profile was successfully updated!",
            extra_tags="alert alert-dismissible alert-success")

        return self.success_url
