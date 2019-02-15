#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 15:33:34 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse

from validation.models import ValidationResult as ValidationResultModel
from image_app.models import STATUSES

# Get an instance of a logger
logger = logging.getLogger(__name__)

# get status
NEED_REVISION = STATUSES.get_value('need_revision')


# a mixin to isolate user data
class OwnerMixin(LoginRequiredMixin):
    def get_queryset(self):
        qs = super(OwnerMixin, self).get_queryset()
        logger.debug("Checking '%s' ownership for user '%s'" % (
            self.request.path, self.request.user))
        return qs.filter(owner=self.request.user)


class DetailMaterialMixin(OwnerMixin):
    """A common DetailMixin for Material classes (Sample/Animal)"""

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

        qs = super(DetailMaterialMixin, self).get_queryset()
        return qs.select_related(
            "name",
            "name__validationresult",
            "name__submission")


class UpdateMaterialMixin(OwnerMixin):
    """A common UpdateMixin for Material classes (Sample/Animal)"""

    def dispatch(self, request, *args, **kwargs):
        handler = super(UpdateMaterialMixin, self).dispatch(
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

    # add the request to the kwargs
    # https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    def get_form_kwargs(self):
        kwargs = super(UpdateMaterialMixin, self).get_form_kwargs()
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


class DeleteMaterialMixin(OwnerMixin):
    """A common DeleteMixin for Material classes (Sample/Animal)"""

    def dispatch(self, request, *args, **kwargs):
        handler = super(DeleteMaterialMixin, self).dispatch(
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


class ListMaterialMixin(OwnerMixin):
    """A common ListMixin for Material classes (Sample/Animal)"""

    def get_queryset(self):
        """Override get_queryset"""

        qs = super(ListMaterialMixin, self).get_queryset()
        return qs.select_related(
            "name",
            "name__validationresult",
            "name__submission")
