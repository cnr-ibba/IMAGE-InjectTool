#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 16:25:59 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.views.generic import DetailView, UpdateView, DeleteView, ListView

from image_app.models import Sample
from common.views import (
    DetailMaterialMixin, UpdateMaterialMixin, DeleteMaterialMixin,
    ListMaterialMixin)

from .forms import UpdateSampleForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


class DetailSampleView(DetailMaterialMixin, DetailView):
    model = Sample
    template_name = "samples/sample_detail.html"


class UpdateSampleView(UpdateMaterialMixin, UpdateView):
    form_class = UpdateSampleForm
    model = Sample
    template_name = "samples/sample_form.html"


class DeleteSampleView(DeleteMaterialMixin, DeleteView):
    model = Sample
    template_name = "samples/sample_confirm_delete.html"


class ListSampleView(ListMaterialMixin, ListView):
    model = Sample
    template_name = "samples/sample_list.html"
    paginate_by = 10
    ordering = ["name__submission"]
