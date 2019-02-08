#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 12:34:22 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.contrib import messages
from django.views.generic import DetailView, UpdateView, DeleteView, ListView

from image_app.models import Animal
from common.views import OwnerMixin

from .forms import UpdateAnimalForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


class DetailAnimalView(OwnerMixin, DetailView):
    model = Animal
    template_name = "animals/animal_detail.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        # get a validationresult obj
        if hasattr(self.object.name, "validationresult"):
            validation = self.object.name.validationresult

            for message in validation.messages:
                if "Warning:" in message:
                    messages.warning(
                        request=self.request,
                        message=message,
                        extra_tags="alert alert-dismissible alert-warning")

                # the other validation messages are threated like errors
                else:
                    messages.error(
                        request=self.request,
                        message=message,
                        extra_tags="alert alert-dismissible alert-danger")

            # cicle for a message in validation.messages

        # condition: I have validation result
        return data

    def get_queryset(self):
        """Override get_queryset"""

        qs = super(DetailAnimalView, self).get_queryset()
        return qs.select_related(
            "name",
            "name__validationresult",
            "name__submission")


class UpdateAnimalView(OwnerMixin, UpdateView):
    form_class = UpdateAnimalForm
    model = Animal
    template_name = "animals/animal_form.html"

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

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    def get_form_kwargs(self):
        kwargs = super(UpdateAnimalView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    # override UpdateView.get_form() method. Initialize a form object
    # and pass submission into it. Self object is the animal object I
    # want to update
    def get_form(self):
        return self.form_class(
            self.object, **self.get_form_kwargs())


class DeleteAnimalView(OwnerMixin, DeleteView):
    model = Animal
    template_name = "animals/animal_confirm_delete.html"


class AnimaViewlList(OwnerMixin, ListView):
    model = Animal
    template_name = "animals/animal_list.html"
    paginate_by = 10
    ordering = ["name__submission"]

    def get_queryset(self):
        """Override get_queryset"""

        qs = super(AnimaViewlList, self).get_queryset()
        return qs.select_related(
            "name",
            "name__validationresult",
            "name__submission")
