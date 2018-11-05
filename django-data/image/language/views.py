#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  5 14:31:14 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from image_app.models import DictCountry

from .models import SpecieSynonim

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ListSpeciesView(LoginRequiredMixin, ListView):
    model = SpecieSynonim
    template_name = "language/speciesynonim_list.html"
    paginate_by = 10
    ordering = ['word']
    country = None

    queryset = SpecieSynonim.objects.select_related("language", "dictspecie")

    def get_queryset(self):
        # call super method
        queryset = super(ListSpeciesView, self).get_queryset()

        # TODO: remove this
        logger.debug(self.kwargs)
        logger.debug(self.args)
        logger.debug(self.request.GET)
        logger.debug(self.request.GET.urlencode())

        # HINT: add a more useful log

        country = self.request.GET.get('country')

        if country:
            self.country = get_object_or_404(
                DictCountry, label=country)
            queryset = queryset.filter(language=self.country)

        return queryset

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ListSpeciesView, self).get_context_data(**kwargs)
        # Add in the country
        context['country'] = self.country
        return context
