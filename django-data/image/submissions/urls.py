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

    url(r'^(?P<pk>[-\w]+)/delete_animals/$',
        views.DeleteAnimalsView.as_view(),
        name='delete_animals'),

    url(r'^(?P<pk>[-\w]+)/delete_samples/$',
        views.DeleteSamplesView.as_view(),
        name='delete_samples'),

    url(r'^(?P<pk>[-\w]+)/validation_summary/(?P<type>[\w]+)/$',
        views.SubmissionValidationSummaryView.as_view(),
        name='validation_summary'),

    url(r'^(?P<pk>[-\w]+)/batch_delete/(?P<type>[\w]+)/$',
        views.BatchDelete.as_view(),
        name='batch_delete')
]
