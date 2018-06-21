#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 16:54:00 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        r'^my_account/$',
        views.UserUpdateView.as_view(),
        name='my_account'
    ),
]
