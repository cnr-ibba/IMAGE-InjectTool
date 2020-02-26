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
from common.constants import BIOSAMPLE_URL
from uid.models import (
    missing_terms, DictBreed, DictCountry, DictSpecie, DictUberon,
    DictDevelStage, DictPhysioStage)

from .tasks import (
    AnnotateBreeds as AnnotateBreedsTask,
    AnnotateCountries as AnnotateCountriesTask,
    AnnotateSpecies as AnnotateSpeciesTask,
    AnnotateOrganismPart as AnnotateOrganismPartTask,
    AnnotateDevelStage as AnnotateDevelStageTask,
    AnnotatePhysioStage as AnnotatePhysioStageTask
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

        # add the base biosample urls to context
        context["biosample_url"] = BIOSAMPLE_URL + "?filter=attr:project:IMAGE"

        return context


class AnnotateViewMixin():
    # forcing POST methods only
    # https://stackoverflow.com/a/36865283/4385116
    http_method_names = ['post', 'get']
    task_class = None
    task_name = None
    dict_class = None

    def get(self, request):
        missing = self.dict_class.objects.filter(term=None).count()
        total = self.dict_class.objects.count()

        return JsonResponse(
            {'status': 'OK',
             'dict_type': self.dict_class._meta.verbose_name_plural,
             'missing': missing,
             'total': total})

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
    task_name = "Annotate Breeds"
    dict_class = DictBreed


class AnnotateCountriesView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateCountriesTask
    task_name = "Annotate Countries"
    dict_class = DictCountry


class AnnotateSpeciesView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateSpeciesTask
    task_name = "Annotate Species"
    dict_class = DictSpecie


class AnnotateOrganismPartView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateOrganismPartTask
    task_name = "Annotate Organism Parts"
    dict_class = DictUberon


class AnnotateDevelStageView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotateDevelStageTask
    task_name = "Annotate Developmental Stages"
    dict_class = DictDevelStage


class AnnotatePhysioStageView(
        AnnotateViewMixin, LoginRequiredMixin, AjaxTemplateView):

    task_class = AnnotatePhysioStageTask
    task_name = "Annotate Physiological Stages"
    dict_class = DictPhysioStage
