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

    url(r'^annotate_breeds/$',
        views.AnnotateBreedsView.as_view(),
        name='annotate_breeds'),

    url(r'^annotate_countries/$',
        views.AnnotateCountriesView.as_view(),
        name='annotate_countries'),

    url(r'^annotate_species/$',
        views.AnnotateSpeciesView.as_view(),
        name='annotate_species'),

    url(r'^annotate_organismparts/$',
        views.AnnotateOrganismPartView.as_view(),
        name='annotate_organismparts'),

    url(r'^annotate_develstages/$',
        views.AnnotateDevelStageView.as_view(),
        name='annotate_develstages'),

    url(r'^annotate_physiostages/$',
        views.AnnotatePhysioStageView.as_view(),
        name='annotate_physiostages'),
]
