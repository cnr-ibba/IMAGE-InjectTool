#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 15:39:30 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from common.views import AjaxTemplateView
from image_app.models import missing_terms

from .tasks import AnnotateBreeds as AnnotateBreedsTask

# Get an instance of a logger
logger = logging.getLogger(__name__)


class OntologiesReportView(LoginRequiredMixin, TemplateView):
    template_name = 'zooma/ontologies_report.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # call report from UID model
        context["missing_terms"] = missing_terms()

        return context


class AnnotateBreedsView(LoginRequiredMixin, AjaxTemplateView):
    # forcing POST methods only
    # https://stackoverflow.com/a/36865283/4385116
    http_method_names = ['post']

    def post(self, request):
        task = AnnotateBreedsTask()

        res = task.delay()

        logger.info(
            "Start AnnotateBreedsTask %s from user %s" % (
                res.task_id, request.user))

        return JsonResponse({'status': 'AnnotateBreeds Started'})
