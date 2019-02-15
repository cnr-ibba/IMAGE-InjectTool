#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 12:34:22 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.views.generic import DetailView, UpdateView, DeleteView, ListView
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect

from image_app.models import Animal, STATUSES
from common.views import OwnerMixin
from validation.models import ValidationResult as ValidationResultModel

from .forms import UpdateAnimalForm

# Get an instance of a logger
logger = logging.getLogger(__name__)

# get status
NEED_REVISION = STATUSES.get_value('need_revision')


class DetailAnimalView(OwnerMixin, DetailView):
    model = Animal
    template_name = "animals/animal_detail.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        # get a validationresult obj
        if hasattr(self.object.name, "validationresult"):
            validation = self.object.name.validationresult

            logger.debug(
                "Found validationresult: %s->%s" % (
                    validation, validation.messages))

            # I could have more messages in validation message. They could
            # be werning or errors, validation.status (overall status)
            # has no meaning here
            for message in validation.messages:
                if "Info:" in message:
                    messages.info(
                        request=self.request,
                        message=message,
                        extra_tags="alert alert-dismissible alert-info")

                elif "Warning:" in message:
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

    def dispatch(self, request, *args, **kwargs):
        handler = super(UpdateAnimalView, self).dispatch(
                request, *args, **kwargs)

        # here I've done get_queryset. Check for submission status
        if hasattr(self, "object") and not self.object.can_edit():
            message = "Cannot edit %s: submission status is: %s" % (
                    self.object, self.object.submission.get_status_display())

            logger.warning(message)
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

            return redirect(self.object.get_absolute_url())

        return handler

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

    # override form valid istance
    def form_valid(self, form):
        self.object = form.save(commit=False)

        # HINT: validate object?

        # setting statuses and messages
        self.object.name.status = NEED_REVISION
        self.object.name.last_changed = timezone.now()
        self.object.name.save()

        if hasattr(self.object.name, 'validationresult'):
            validationresult = self.object.name.validationresult
        else:
            validationresult = ValidationResultModel()
            self.object.name.validationresult = validationresult

        validationresult.messages = [
            'Info: Data has changed, validation has to be called']
        validationresult.status = "Info"
        validationresult.save()

        # Override submission status
        self.object.submission.status = NEED_REVISION
        self.object.submission.message = (
            "Data has changed, validation has to be called")
        self.object.submission.save()

        # save object and return HttpResponseRedirect(self.get_success_url())
        return super().form_valid(form)


class DeleteAnimalView(OwnerMixin, DeleteView):
    model = Animal
    template_name = "animals/animal_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        handler = super(DeleteAnimalView, self).dispatch(
                request, *args, **kwargs)

        # here I've done get_queryset. Check for submission status
        if hasattr(self, "object") and not self.object.can_edit():
            message = "Cannot delete %s: submission status is: %s" % (
                    self.object, self.object.submission.get_status_display())

            logger.warning(message)
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

            return redirect(self.object.get_absolute_url())

        return handler

    def get_success_url(self):
        return reverse(
            'submissions:edit',
            kwargs={'pk': self.object.submission.pk}
        )

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

        # get the related name object
        name = self.object.name
        logger.debug("Got name: %s" % (name))

        # get its samples and their names
        samples = self.object.sample_set.all()
        logger.debug("Got samples: %s" % (samples))

        # deleting object in a transaction
        with transaction.atomic():
            # delete all child samples
            for sample in samples:
                sample_name = sample.name

                logger.debug(
                    "Deleting sample:%s and name:%s" % (sample, sample_name))

                result = sample.delete()
                logger.debug("%s objects deleted" % str(result))

                result = sample_name.delete()
                logger.debug("%s objects deleted" % str(result))

            # clear all child from this animal
            logger.debug("Clearing all childs from this animal")
            name.mother_of.clear()
            name.father_of.clear()

            # delete this animal object
            logger.debug(
                "Deleting animal:%s and name:%s" % (self.object, name))

            result = self.object.delete()
            logger.debug("%s objects deleted" % str(result))

            result = name.delete()
            logger.debug("%s objects deleted" % str(result))

        message = "Animal %s was successfully deleted" % self.object.name
        logger.info(message)

        messages.info(
            request=self.request,
            message=message,
            extra_tags="alert alert-dismissible alert-info")

        return HttpResponseRedirect(success_url)


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
