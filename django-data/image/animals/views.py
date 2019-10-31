#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 12:34:22 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.db import transaction
from django.contrib import messages
from django.views.generic import DetailView, UpdateView, DeleteView, ListView
from django.http import HttpResponseRedirect

from uid.models import Animal
from common.views import (
    DetailMaterialMixin, UpdateMaterialMixin, DeleteMaterialMixin,
    ListMaterialMixin)
from validation.models import ValidationResult as ValidationResultModel

from .forms import UpdateAnimalForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


class DetailAnimalView(DetailMaterialMixin, DetailView):
    model = Animal
    template_name = "animals/animal_detail.html"


class UpdateAnimalView(UpdateMaterialMixin, UpdateView):
    form_class = UpdateAnimalForm
    model = Animal
    template_name = "animals/animal_form.html"

    # specify a real validation class for update
    validationresult_class = ValidationResultModel

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """

        initial = super(UpdateAnimalView, self).get_initial()

        # Add name, mother, father
        initial['disabled_name'] = self.object.name
        initial['disabled_mother'] = self.object.mother
        initial['disabled_father'] = self.object.father

        return initial


class DeleteAnimalView(DeleteMaterialMixin, DeleteView):
    model = Animal
    template_name = "animals/animal_confirm_delete.html"

    # ovverride the default detail method.
    # HINT: Suppose I want to delete an animal
    # that is mother or father of another one. Should I delete its child
    # element? for the moment, I will disconnect all its child from this
    # object. All its child will have unknown father and mother
    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object, does all stuff and
        then redirects to the success URL.
        """

        self.object = self.get_object()
        logger.debug("Got animal: %s" % (self.object))
        success_url = self.get_success_url()

        # get its samples and their names
        samples = self.object.sample_set.all()
        logger.debug("Got samples: %s" % (samples))

        # deleting object in a transaction
        with transaction.atomic():
            # delete all child samples
            for sample in samples:
                logger.debug(
                    "Deleting sample:%s" % (sample))

                result = sample.delete()
                logger.debug("%s objects deleted" % str(result))

            # clear all child from this animal
            logger.debug("Clearing all childs from this animal")
            self.object.mother_of.clear()
            self.object.father_of.clear()

            # delete this animal object
            logger.debug(
                "Deleting animal:%s" % (self.object))

            result = self.object.delete()
            logger.debug("%s objects deleted" % str(result))

        message = "Animal %s was successfully deleted" % self.object.name
        logger.info(message)

        messages.info(
            request=self.request,
            message=message,
            extra_tags="alert alert-dismissible alert-info")

        return HttpResponseRedirect(success_url)


class ListAnimalView(ListMaterialMixin, ListView):
    model = Animal
    template_name = "animals/animal_list.html"
    paginate_by = 10
    ordering = ["name__submission"]

    def get_queryset(self):
        """Override get_queryset"""

        qs = super(ListAnimalView, self).get_queryset()
        return qs.select_related(
            "name",
            "name__validationresult",
            "name__submission")
