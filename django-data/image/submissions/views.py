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

    # when a model is specified, the template_name is derived from it
    # template_name will be 'submission_form.html'


class DetailSubmissionView(LoginRequiredMixin, DetailView):
    model = Submission

    # template_name will be 'submission_detail.html'


class ListSubmissionsView(LoginRequiredMixin, ListView):
    model = Submission

    # template_name will be 'submission_list.html'
