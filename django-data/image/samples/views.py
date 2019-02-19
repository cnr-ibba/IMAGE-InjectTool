#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 16:25:59 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.db import transaction
from django.contrib import messages
from django.views.generic import DetailView, UpdateView, DeleteView, ListView
from django.http import HttpResponseRedirect

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

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """

        initial = super(UpdateSampleView, self).get_initial()

        # Add name, animal
        initial['disabled_name'] = self.object.name
        initial['disabled_animal'] = self.object.animal

        return initial


class DeleteSampleView(DeleteMaterialMixin, DeleteView):
    model = Sample
    template_name = "samples/sample_confirm_delete.html"

    # ovverride the default detail method.
    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object, does all stuff and
        then redirects to the success URL.
        """

        self.object = self.get_object()
        logger.debug("Got sample: %s" % (self.object))
        success_url = self.get_success_url()

        # get the related name object
        name = self.object.name
        logger.debug("Got name: %s" % (name))

        # deleting object in a transaction
        with transaction.atomic():
            # delete this sample object
            logger.debug(
                "Deleting sample:%s and name:%s" % (self.object, name))

            result = self.object.delete()
            logger.debug("%s objects deleted" % str(result))

            result = name.delete()
            logger.debug("%s objects deleted" % str(result))

        message = "Sample %s was successfully deleted" % self.object.name
        logger.info(message)

        messages.info(
            request=self.request,
            message=message,
            extra_tags="alert alert-dismissible alert-info")

        return HttpResponseRedirect(success_url)


class ListSampleView(ListMaterialMixin, ListView):
    model = Sample
    template_name = "samples/sample_list.html"
    paginate_by = 10
    ordering = ["name__submission"]
