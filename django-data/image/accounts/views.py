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
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

from registration import signals
from registration.backends.default.views import \
    ActivationView as RegistrationActivationView
from registration.backends.default.views import RegistrationView

from .forms import MyAccountForm, SignUpForm


class SignUpView(RegistrationView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = 'accounts:registration_complete'

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    def get_form_kwargs(self):
        kwargs = super(SignUpView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # Save the user first, because the profile needs a user before it
        # can be saved. When I save user, I save also person since is related
        # to user. Calling register custom method
        user = self.register(form['user'])

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

        success_url = self.get_success_url(user)

        # success_url may be a simple string, or a tuple providing the
        # full argument set for redirect(). Attempting to unpack it
        # tells us which one it is.
        try:
            to, args, kwargs = success_url
        except ValueError:
            return redirect(success_url)
        else:
            return redirect(to, *args, **kwargs)

    def form_invalid(self, form):
        messages.error(
            self.request,
            message="Please correct the errors below",
            extra_tags="alert alert-dismissible alert-danger")

        return super(SignUpView, self).form_invalid(form)

    def register(self, form):
        """
        Given a username, email address and password, register a new
        user account, which will initially be inactive.
        Along with the new ``User`` object, a new
        ``registration.models.RegistrationProfile`` will be created,
        tied to that ``User``, containing the activation key which
        will be used for this account.
        An email will be sent to the supplied email address; this
        email should contain an activation link. The email will be
        rendered using two templates. See the documentation for
        ``RegistrationProfile.send_activation_email()`` for
        information about these templates and the contexts provided to
        them.
        After the ``User`` and ``RegistrationProfile`` are created and
        the activation email is sent, the signal
        ``registration.signals.user_registered`` will be sent, with
        the new ``User`` as the keyword argument ``user`` and the
        class of this backend as the sender.
        """
        site = get_current_site(self.request)

        new_user_instance = form.save()

        new_user = self.registration_profile.objects.create_inactive_user(
            new_user=new_user_instance,
            site=site,
            send_email=self.SEND_ACTIVATION_EMAIL,
            request=self.request,
        )

        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=self.request)
        return new_user


# re-define activation view
class ActivationView(RegistrationActivationView):
    success_url = 'accounts:registration_activation_complete'

    def get_success_url(self, user):
        return (self.success_url, (), {})


# dispatch is an internal method Django use (defined inside the View class)
# transaction atomic allows us to create a block of code within which the
# atomicity on the database is guaranteedIf the block of code is successfully
# completed, the changes are committed to the database
@method_decorator(login_required, name='dispatch')
class MyAccountView(UpdateView):
    # applying user model (that has relation with person model)
    # I need a model instance to work with UpdateView
    model = get_user_model()

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
