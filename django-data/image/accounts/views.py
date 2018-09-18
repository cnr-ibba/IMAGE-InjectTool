#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 16:04:02 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

inspired from A Complete Beginner's Guide to Django - Part 4

https://simpleisbetterthancomplex.com/series/2017/09/25/a-complete-beginners-guide-to-django-part-4.html

"""

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.views.generic.base import TemplateView

from registration import signals
from registration.backends.default.views import (
    ActivationView as RegistrationActivationView,
    ResendActivationView as BaseResendActivationView)
from registration.backends.default.views import RegistrationView

from .forms import MyAccountForm, SignUpForm
from .models import MyRegistrationProfile


# Get an instance of a logger
logger = logging.getLogger(__name__)


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

        logger.debug("Updated user infos")

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

        logger.info("registering user: %s" % (new_user_instance))

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

    # override template
    template_name = 'registration/activation_failed.html'

    # ovveride django redux get method
    def get(self, request, *args, **kwargs):
        activated_user = self.activate(*args, **kwargs)

        if activated_user:
            logger.info("%s activated" % activated_user)
            success_url = self.get_success_url(activated_user)
            try:
                to, args, kwargs = success_url
            except ValueError:
                return redirect(success_url)
            else:
                return redirect(to, *args, **kwargs)

        # if I arrive here, user is not activated. Maybe the keys is not more
        # valid or there isn't such key in the database
        logger.error("Error for key: %s" % kwargs.get('activation_key', ''))
        return super(ActivationView, self).get(request, *args, **kwargs)

    def get_success_url(self, user):
        # authenticate the user using the provided key
        auth_login(self.request, user)
        return (self.success_url, (), {})

    # Override activate function
    def activate(self, *args, **kwargs):
        """
        Given an an activation key, look up and activate the user
        account corresponding to that key (if possible).

        After successful activation, the signal
        ``registration.signals.user_activated`` will be sent, with the
        newly activated ``User`` as the keyword argument ``user`` and
        the class of this backend as the sender.

        """
        activation_key = kwargs.get('activation_key', '')
        site = get_current_site(self.request)
        user, activated = self.registration_profile.objects.activate_user(
            activation_key, site)

        if activated:
            signals.user_activated.send(sender=self.__class__,
                                        user=user,
                                        request=self.request)

        if user and not activated:
            # this could be an activated user trying the same key used for
            # activation
            logger.warning("key %s already used by %s" % (
                activation_key, user))

            messages.warning(
                self.request,
                message="Activation key already used",
                extra_tags="alert alert-dismissible alert-warning")

        return user


# override redux activation view
class ResendActivationView(BaseResendActivationView):
    registration_profile = MyRegistrationProfile

    def form_valid(self, form):
        """
        Regardless if resend_activation is successful, display the same
        confirmation template.

        """

        success, reason = self.resend_activation(form)
        if not success:
            form.add_error(
                'email',
                reason)
            return self.form_invalid(form)

        return self.render_form_submitted_template(form)

    def render_form_submitted_template(self, form):
        """
        Renders resend activation complete template with the submitted email.

        """

        return render(self.request,
                      'registration/resend_activation_complete.html')


class ActivationComplete(LoginRequiredMixin, TemplateView):
    template_name = 'registration/activation_complete.html'


# LoginRequiredMixin as the letfmost inherited module. It will provide
# authentication methods
class MyAccountView(LoginRequiredMixin, UpdateView):
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
