#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  5 14:16:22 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^species/$',
        views.ListSpeciesView.as_view(),
        name='species'),
]
