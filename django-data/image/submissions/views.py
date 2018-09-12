#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 15:49:23 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView

from image_app.models import Submission
from .forms import SubmissionForm


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
        # call inherited methods (which save object and render Http)
        # a valid submission returns a submission detail view
        # through get_absolute_url defined in Submission model method

        # TODO: remove form:valid super method, save object, call the upload
        # task then return success url
        return super().form_valid(form)

        # TODO: a valid submission start a task
        # TODO: call task
        # self.object = form.save()
        # return HttpResponseRedirect(self.get_success_url())


class DetailSubmissionView(LoginRequiredMixin, DetailView):
    model = Submission
    template_name = "submissions/submission_detail.html"


class ListSubmissionsView(LoginRequiredMixin, ListView):
    model = Submission
    template_name = "submissions/submission_list.html"
