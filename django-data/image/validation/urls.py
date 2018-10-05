#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 12:21:38 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        r'^validate$',
        views.ValidateView.as_view(),
        name='validate'
    ),
]
