#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 18 16:38:35 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.conf.urls import url

from . import views

# TODO: those views will be removed when data import and database task will be
# addressed using celery modules
urlpatterns = [
    url(r'^import_from_cryoweb/$',
        views.import_from_cryoweb,
        name='import_from_cryoweb'),

    url(r'^truncate_cryoweb_tables/$',
        views.truncate_cryoweb_tables,
        name='truncate_cryoweb_tables'),
]
