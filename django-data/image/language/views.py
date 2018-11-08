#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  5 14:31:14 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView

from image_app.models import DictCountry

from .models import SpecieSynonim
from .forms import SpecieSynonimForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


class CountryMixin(object):
    """Read country label from request get (if present) and add to context"""

    country = None

    # perform a join while getting queryset
    queryset = SpecieSynonim.objects.select_related("language", "dictspecie")

    def get_queryset(self):
        """Read country if requested suing GET method"""

        # call super method
        queryset = super(CountryMixin, self).get_queryset()

        # get country or none from a get request
        country = self.request.GET.get('country')

        if country:
            self.country = get_object_or_404(
                DictCountry, label=country)
            queryset = queryset.filter(language=self.country)

        return queryset

    def get_context_data(self, **kwargs):
        """Add a dictcountry object to a context"""

        # Call the base implementation first to get a context
        context = super(CountryMixin, self).get_context_data(**kwargs)

        # Add my country attribute to context
        context['country'] = self.country

        return context


class ListSpeciesView(LoginRequiredMixin, CountryMixin, ListView):
    model = SpecieSynonim
    template_name = "language/speciesynonim_list.html"
    paginate_by = 10
    ordering = ['word']


class UpdateSpeciesView(LoginRequiredMixin, CountryMixin, UpdateView):
    form_class = SpecieSynonimForm
    template_name = "language/speciesynonim_form.html"

    # https://stackoverflow.com/a/31275770/4385116
    # You can't use reverse with success_url, because then reverse is
    # called when the module is imported, before the urls have been loaded.
    success_url = reverse_lazy("language:species")

    def get_success_url(self):
        """Redirect to page if form is valid"""

        success_url = self.success_url

        if self.country:
            success_url += "?country={country}".format(
                country=self.country.label)

        return success_url
