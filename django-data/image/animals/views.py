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


class UpdateAnimalView(OwnerMixin, UpdateView):
    model = Animal
    fields = '__all__'
    template_name = "animals/animal_form.html"


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
