#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 16:54:00 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView

from registration.backends.default.views import ResendActivationView

from . import views

urlpatterns = [
    url(r'^password_change/$',
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            success_url=reverse_lazy('accounts:password_change_done')
        ),
        name='password_change'),

    url(r'^password_change/done/$',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html'),
        name='password_change_done'),

    url(r'^password_reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('accounts:password_reset_done')
        ),
        name='password_reset'),

    url(r'^password_reset/done/$',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_done'),

    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}'
        '-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete')
            ),
        name='password_reset_confirm'),

    url(r'^reset/done/$',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete'),

    url(
        r'^my_account/$',
        views.MyAccountView.as_view(),
        name='my_account'
    ),
    url(
        r'^register/$',
        views.SignUpView.as_view(),
        name='registration_register'
    ),
    # Using registration redux urls
    url(r'^activate/complete/$',
        TemplateView.as_view(
            template_name='registration/activation_complete.html'),
        name='registration_activation_complete'),
    url(r'^activate/resend/$',
        ResendActivationView.as_view(),
        name='registration_resend_activation'),

    # Activation keys get matched by \w+ instead of the more specific
    # [a-fA-F0-9]{40} because a bad activation key should still get to the
    # view; that way it can return a sensible "invalid key" message instead
    # of a confusing 404.
    url(r'^activate/(?P<activation_key>\w+)/$',
        views.ActivationView.as_view(),
        name='registration_activate'),
    url(r'^register/complete/$',
        TemplateView.as_view(
            template_name='registration/registration_complete.html'),
        name='registration_complete'),
    url(r'^register/closed/$',
        TemplateView.as_view(
            template_name='registration/registration_closed.html'),
        name='registration_disallowed'),
]
