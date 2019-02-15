#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 16:25:59 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.views.generic import DetailView, UpdateView, DeleteView, ListView

from common.views import OwnerMixin
from image_app.models import Sample, STATUSES

from .forms import UpdateSampleForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


class DetailSampleView(OwnerMixin, DetailView):
    model = Sample
    template_name = "samples/sample_detail.html"


class UpdateSampleView(OwnerMixin, UpdateView):
    form_class = UpdateSampleForm
    model = Sample
    template_name = "samples/sample_form.html"


class DeleteSampleView(OwnerMixin, DeleteView):
    model = Sample
    template_name = "samples/sample_confirm_delete.html"


class ListSampleView(OwnerMixin, ListView):
    model = Sample
    template_name = "samples/sample_list.html"
    paginate_by = 10
    ordering = ["name__submission"]

    def get_queryset(self):
        """Override get_queryset"""

        qs = super(ListSampleView, self).get_queryset()
        return qs.select_related(
            "name",
            "name__validationresult",
            "name__submission")
