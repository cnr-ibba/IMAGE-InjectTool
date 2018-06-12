#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 17:06:59 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        r'^token/generate$',
        views.CreateAuthView.as_view(),
        name='token-generation'
    ),
    url(
        r'^token/$',
        views.AuthView.as_view(),
        name='token'
    ),
]
