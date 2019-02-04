#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 12:31:06 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<pk>[-\w]+)/$',
        views.DetailAnimalView.as_view(),
        name='detail'),
]
