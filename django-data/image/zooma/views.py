#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 15:39:30 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class OntologiesReportView(LoginRequiredMixin, TemplateView):
    template_name = 'zooma/ontologies_report.html'
