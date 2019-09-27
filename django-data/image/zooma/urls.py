#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 15:46:59 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.conf.urls import url

from . import views

# from django.conf.urls import include
# from django.contrib import admin


urlpatterns = [
    url(r'^ontologies_report/$',
        views.OntologiesReportView.as_view(),
        name='ontologies_report'),
]
