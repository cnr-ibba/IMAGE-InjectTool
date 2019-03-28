#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:51:13 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^create/$',
        views.CreateSubmissionView.as_view(),
        name='create'),

    url(r'^list/$',
        views.ListSubmissionsView.as_view(),
        name='list'),

    url(r'^(?P<pk>[-\w]+)/$',
        views.DetailSubmissionView.as_view(),
        name='detail'),

    url(r'^(?P<pk>[-\w]+)/edit/$',
        views.EditSubmissionView.as_view(),
        name='edit'),

    url(r'^(?P<pk>[-\w]+)/reload/$',
        views.ReloadSubmissionView.as_view(),
        name='reload'),
    url(r'^(?P<pk>[-\w]+)/delete/$',
        views.DeleteSubmissionView.as_view(),
        name='delete'),
]
