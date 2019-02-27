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
from django.shortcuts import get_object_or_404, redirect

from common.constants import (
    WAITING, ERROR, SUBMITTED, NEED_REVISION, CRYOWEB_TYPE)
from common.views import OwnerMixin
from cryoweb.tasks import import_from_cryoweb
from image_app.models import Submission, Name

from .forms import SubmissionForm, ReloadForm

# Get an instance of a logger
logger = logging.getLogger(__name__)


class CreateSubmissionView(LoginRequiredMixin, CreateView):
    form_class = SubmissionForm
    model = Submission

    # template name is derived from model position and views type.
    # in this case, ir will be 'image_app/submission_form.html' so
    # i need to clearly specify it
    template_name = "submissions/submission_form.html"

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """

        initial = super(CreateSubmissionView, self).get_initial()

        # set initial value for datasource type
        initial['datasource_type'] = CRYOWEB_TYPE

        return initial

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


class MessagesSubmissionMixin(object):
    """Display messages in SubmissionViews"""

    # https://stackoverflow.com/a/45696442
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        # get the submission message
        message = self.submission.message

        # check if data are loaded or not
        if self.submission.status in [WAITING, SUBMITTED]:
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

        elif self.submission.status in [ERROR, NEED_REVISION]:
            messages.error(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-danger")

        elif message is not None and message != '':
            messages.info(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-info")

        return data


class DetailSubmissionView(MessagesSubmissionMixin, OwnerMixin, DetailView):
    model = Submission
    template_name = "submissions/submission_detail.html"

    def get_context_data(self, **kwargs):
        # pass self.object to a new submission attribute in order to call
        # MessagesSubmissionMixin.get_context_data()
        self.submission = self.object

        # Call the base implementation first to get a context
        return super(DetailSubmissionView, self).get_context_data(**kwargs)


# a detail view since I need to operate on a submission object
# HINT: rename to a more informative name?
class EditSubmissionView(MessagesSubmissionMixin, OwnerMixin, ListView):
    template_name = "submissions/submission_edit.html"
    paginate_by = 10

    def get_queryset(self):
        """Subsetting names relying submission id"""
        self.submission = get_object_or_404(
            Submission,
            pk=self.kwargs['pk'],
            owner=self.request.user)

        # unknown animals should be removed from a submission. They have no
        # data in animal table nor sample
        return Name.objects.select_related(
                "validationresult",
                "animal",
                "sample").filter(
            Q(submission=self.submission) & (
                Q(animal__isnull=False) | Q(sample__isnull=False))
            ).order_by('id')

    def dispatch(self, request, *args, **kwargs):
        handler = super(EditSubmissionView, self).dispatch(
                request, *args, **kwargs)

        # here I've done get_queryset. Check for submission status
        if hasattr(self, "submission") and not self.submission.can_edit():
            message = "Cannot edit submission: current status is: %s" % (
                    self.submission.get_status_display())

            logger.warning(message)
            messages.warning(
                request=self.request,
                message=message,
                extra_tags="alert alert-dismissible alert-warning")

            return redirect(self.submission.get_absolute_url())

        return handler

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(EditSubmissionView, self).get_context_data(**kwargs)

        # add submission to context
        context["submission"] = self.submission

        return context


class ListSubmissionsView(OwnerMixin, ListView):
    model = Submission
    template_name = "submissions/submission_list.html"
    ordering = ['-created_at']
    paginate_by = 10


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
