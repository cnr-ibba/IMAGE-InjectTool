#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:34 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.urls import reverse

from image_app.models import Submission

from .forms import ValidateForm
from .tasks import validate_submission

# Get an instance of a logger
logger = logging.getLogger(__name__)

# reading statuses
WAITING = Submission.STATUSES.get_value('waiting')


class ValidateView(LoginRequiredMixin, FormView):
    form_class = ValidateForm
    template_name = 'validation/validate.html'
    submission_id = None

    def get_success_url(self):
        return reverse('submissions:detail', kwargs={
            'pk': self.submission_id})

    def form_valid(self, form):
        submission_id = form.cleaned_data['submission_id']
        submission = Submission.objects.get(pk=submission_id)

        # TODO: check if I can validate object (statuses)

        submission.message = "waiting for data validation"
        submission.status = WAITING
        submission.save()

        # a valid submission start a task
        res = validate_submission.delay(submission_id)
        logger.info(
            "Start validation process for %s with task %s" % (
                submission,
                res.task_id))

        # track submission id in order to render page
        self.submission_id = submission_id

        return super(ValidateView, self).form_valid(form)
