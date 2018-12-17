#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:49:23 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.shortcuts import get_object_or_404

from cryoweb.tasks import import_from_cryoweb
from image_app.models import Submission, STATUSES, Name
from common.views import OwnerMixin

from .forms import SubmissionForm, ReloadForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


# reading statuses
WAITING = STATUSES.get_value('waiting')
ERROR = STATUSES.get_value('error')
SUBMITTED = STATUSES.get_value('submitted')
NEED_REVISION = STATUSES.get_value('need_revision')

CRYOWEB_TYPE = Submission.TYPES.get_value('cryoweb')


class CreateSubmissionView(LoginRequiredMixin, CreateView):
    form_class = SubmissionForm
    model = Submission

    # template name is derived from model position and views type.
    # in this case, ir will be 'image_app/submission_form.html' so
    # i need to clearly specify it
    template_name = "submissions/submission_form.html"

    # add user to this object
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user

        # I will have a different loading function accordingly with data type
        if self.object.datasource_type == CRYOWEB_TYPE:
            # update object and force status
            self.object.message = "waiting for data loading"
            self.object.status = WAITING
            self.object.save()

            # a valid submission start a task
            res = import_from_cryoweb.delay(self.object.pk)
            logger.info(
                "Start cryoweb importing process with task %s" % res.task_id)

        else:
            message = "{datasource} import is not implemented".format(
                datasource=self.object.get_datasource_type_display())

            self.object.message = message
            self.object.status = ERROR
            self.object.save()

            logger.error(message)

        # a redirect to self.object.get_absolute_url()
        return HttpResponseRedirect(self.get_success_url())


class DetailSubmissionView(OwnerMixin, DetailView):
    model = Submission
    template_name = "submissions/submission_detail.html"

    # https://stackoverflow.com/a/45696442
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        # check if data are loaded or not
        if self.object.status in [WAITING, SUBMITTED]:
            # get the message
            message = self.object.message

            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

        elif self.object.status in [ERROR, NEED_REVISION]:
            messages.error(
                request=self.request,
                message=self.object.message,
                extra_tags="alert alert-dismissible alert-danger")

        elif self.object.message is not None and self.object.message != '':
            messages.debug(
                request=self.request,
                message=self.object.message,
                extra_tags="alert alert-dismissible alert-light")

        return data


class ListSubmissionsView(OwnerMixin, ListView):
    model = Submission
    template_name = "submissions/submission_list.html"
    ordering = ['-created_at']
    paginate_by = 10


# a detail view since I need to operate on a submission object
# HINT: rename to a more informative name?
class EditSubmissionView(OwnerMixin, ListView):
    template_name = "submissions/submission_edit.html"

    def get_queryset(self):
        """Subsetting names relying submission id"""
        self.submission = get_object_or_404(
            Submission,
            pk=self.kwargs['pk'],
            owner=self.request.user)

        # unknown animals should be removed from a submission. They have no
        # data in animal table nor sample
        return Name.objects.filter(
            Q(submission=self.submission) & (
                Q(animal__isnull=False) | Q(sample__isnull=False))
            )

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(EditSubmissionView, self).get_context_data(**kwargs)

        # add submission to context
        context["submission"] = self.submission

        return context


class ReloadSubmissionView(OwnerMixin, UpdateView):
    form_class = ReloadForm
    model = Submission
    template_name = 'submissions/submission_reload.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # update object and force status
        self.object.message = "waiting for data loading"
        self.object.status = WAITING
        self.object.save()

        # a valid submission start a task
        res = import_from_cryoweb.delay(self.object.pk)
        logger.info(
            "Start cryoweb reload process with task %s" % res.task_id)

        # a redirect to self.object.get_absolute_url()
        return HttpResponseRedirect(self.get_success_url())
