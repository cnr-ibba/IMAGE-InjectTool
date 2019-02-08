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
    url(r'^(?P<pk>[-\w]+)/update/$',
        views.UpdateAnimalView.as_view(),
        name='update'),
    url(r'^(?P<pk>[-\w]+)/delete/$',
        views.DeleteAnimalView.as_view(),
        name='delete'),
    url(r'list$',
        views.AnimaViewlList.as_view(),
        name='list'),
]
