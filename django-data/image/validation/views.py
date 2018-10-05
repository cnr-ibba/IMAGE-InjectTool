#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 11:39:34 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from .forms import ValidateForm


class ValidateView(LoginRequiredMixin, FormView):
    form_class = ValidateForm
    template_name = 'validation/validate.html'
    submission_id = None

    def get_success_url(self):
        return reverse_lazy('submissions:detail', kwargs={
            'pk': self.submission_id})

    def form_valid(self, form):
        self.submission_id = form.cleaned_data['submission_id']

        return super(ValidateView, self).form_valid(form)
