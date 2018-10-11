#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 15:04:07 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from cryoweb.models import db_has_data as cryoweb_has_data

from ..models import Submission, uid_report

# Get an instance of a logger
logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    # Just set this Class Object Attribute to the template page.
    # template_name = 'app_name/site.html'
    template_name = 'image_app/index.html'


class AboutView(TemplateView):
    # Just set this Class Object Attribute to the template page.
    # template_name = 'app_name/site.html'
    template_name = 'image_app/about.html'


class DashBoardView(LoginRequiredMixin, TemplateView):
    template_name = "image_app/dashboard.html"

    # I will check if I have submissions or not. If yes, I will set True
    # to a context variable. In the dashboard template I will render the link
    # active only if I have submissions
    # TODO: update for user submission
    # HINT: render this with a custom template tags
    def get_context_data(self, **kwargs):
        kwargs['have_submission'] = Submission.objects.exists()
        return super().get_context_data(**kwargs)


class SummaryView(LoginRequiredMixin, TemplateView):
    template_name = "image_app/summary.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SummaryView, self).get_context_data(**kwargs)
        # add content to context

        # Add info for datasource
        # TODO: count object for a certain user
        context['datasource_count'] = Submission.objects.count()

        # count loaded objects into biosample
        completed = Submission.STATUSES.get_value('completed')
        context['datasource_completed'] = Submission.objects.filter(
            status=completed).count()

        # add info for cryoweb db
        context["cryoweb_hasdata"] = False
        if cryoweb_has_data():
            logger.debug("Cryoweb has data!")
            context["cryoweb_hasdata"] = True

        # call report from UID model
        context["uid_report"] = uid_report()

        return context
