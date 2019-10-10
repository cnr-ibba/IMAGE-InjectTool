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

from .tasks import (
    AnnotateBreeds as AnnotateBreedsTask,
    AnnotateCountries as AnnotateCountriesTask,
    AnnotateSpecies as AnnotateSpeciesTask,
    AnnotateUberon as AnnotateUberonTask,
    AnnotateDictDevelStage as AnnotateDictDevelStageTask,
    AnnotateDictPhysioStage as AnnotateDictPhysioStageTask
)

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


class AnnotateViewMixin():
    # forcing POST methods only
    # https://stackoverflow.com/a/36865283/4385116
    http_method_names = ['post']
    task_class = None
    task_name = None

    def post(self, request):
        task = self.task_class()

        res = task.delay()

        logger.info(
            "Start %s task %s from user %s" % (
                self.task_name, res.task_id, request.user))

        return JsonResponse({'status': '%s started' % (self.task_name)})


class AnnotateBreedsView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateBreedsTask
    task_name = "AnnotateBreeds"


class AnnotateCountriesView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateCountriesTask
    task_name = "AnnotateCountries"


class AnnotateSpeciesView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateSpeciesTask
    task_name = "AnnotateSpecies"


class AnnotateUberonView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateUberonTask
    task_name = "AnnotateUberon"


class AnnotateDictDevelStageView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateDictDevelStageTask
    task_name = "AnnotateDictDevelStage"


class AnnotateDictPhysioStageView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateDictPhysioStageTask
    task_name = "AnnotateDictPhysioStage"
