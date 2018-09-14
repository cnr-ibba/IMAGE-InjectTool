#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:49:23 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView

from cryoweb.tasks import import_from_cryoweb
from image_app.models import Submission

from .forms import SubmissionForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


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

        # update object
        self.object = form.save()

        # a valid submission start a task
        res = import_from_cryoweb.delay(self.object.pk)
        logger.info(
            "Start cryoweb importing process using with task %s" % res.task_id)

        # a redirect to self.object.get_absolute_url()
        return HttpResponseRedirect(self.get_success_url())


class DetailSubmissionView(LoginRequiredMixin, DetailView):
    model = Submission
    template_name = "submissions/submission_detail.html"

    # https://stackoverflow.com/a/45696442
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        if self.object.errors is not None:
            messages.error(
                request=self.request,
                message='Error in importing data: %s' % self.object.errors,
                extra_tags="alert alert-dismissible alert-danger")

            # TODO: add errors to context

        # check if data are loaded or not
        elif self.object.loaded is False:
            messages.warning(
                request=self.request,
                message='waiting for data processing',
                extra_tags="alert alert-dismissible alert-warning")

        return data


class ListSubmissionsView(LoginRequiredMixin, ListView):
    model = Submission
    template_name = "submissions/submission_list.html"
    ordering = ['created_at']
