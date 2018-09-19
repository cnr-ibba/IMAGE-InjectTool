#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 15:04:07 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.management import call_command
from django.shortcuts import redirect
from django.views.generic import TemplateView

from ..helpers import CryowebDB
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

        # count not waiting objects. Using q for a not equal condition
        waiting = Submission.STATUSES.get_value('waiting')
        context['datasource_uploaded'] = Submission.objects.exclude(
            status=waiting).count()

        # add info for cryoweb db
        context["cryoweb_hasdata"] = False
        cryowebdb = CryowebDB()
        if cryowebdb.has_data(search_path='apiis_admin'):
            logger.debug("Cryoweb has data!")
            context["cryoweb_hasdata"] = True

        # call report from UID model
        context["uid_report"] = uid_report()

        return context


@login_required
def truncate_databases(request):
    """ truncate cryoweb and image tables

    this fx calls the custom functions truncate_cryoweb_tables and
    truncate_image_tables, defined in
    image_app/management/commands/truncate_cryoweb_tables.py and
    image_app/management/commands/truncate_image_tables.py
    in order to have the same fx "command line" is necessary to call both
    $ docker-compose run --rm uwsgi python manage.py truncate_cryoweb_tables
    $ docker-compose run --rm uwsgi python manage.py truncate_image_tables

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    call_command('truncate_cryoweb_tables')

    messages.success(
        request,
        message="cryoweb database was truncated with success",
        extra_tags="alert alert-dismissible alert-success")

    call_command('truncate_image_tables')

    messages.success(
        request,
        message="image database was truncated with success",
        extra_tags="alert alert-dismissible alert-success")

    return redirect('image_app:dashboard')


# TODO: this will be removed in production
@login_required
def truncate_image_tables(request):
    """ truncate image tables

    this fx calls the custom function truncate_image_tables, defined in
    image_app/management/commands/truncate_image_tables.py
    this fx can also be called command line as
    $ docker-compose run --rm uwsgi python manage.py truncate_image_tables

    :param request: HTTP request automatically sent by the framework
    :return: the resulting HTML page
    """

    # TODO: move commands to a function
    call_command('truncate_image_tables')

    messages.success(
        request,
        message="image database was truncated with success",
        extra_tags="alert alert-dismissible alert-success")

    return redirect('image_app:dashboard')


# TODO: this will be removed in production
@login_required
def initializedb(request):
    """initialize UID database after truncating image tables"""

    # TODO: move commands to a function
    call_command('initializedb')

    messages.success(
        request,
        message="image database correctly initialized",
        extra_tags="alert alert-dismissible alert-success")

    return redirect('image_app:dashboard')
