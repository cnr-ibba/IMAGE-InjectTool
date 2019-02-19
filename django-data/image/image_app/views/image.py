#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 15:04:07 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

import os
import logging

from django.utils.encoding import smart_str
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.conf import settings
from django.http import HttpResponse

from common.storage import ProtectedFileSystemStorage
from common.constants import COMPLETED

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


class SummaryView(LoginRequiredMixin, TemplateView):
    template_name = "image_app/summary.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SummaryView, self).get_context_data(**kwargs)
        # add content to context

        # Add info for datasource
        # count object for a certain user
        context['datasource_count'] = Submission.objects.filter(
            owner=self.request.user).count()

        # count loaded objects into biosample
        context['datasource_completed'] = Submission.objects.filter(
            status=COMPLETED, owner=self.request.user).count()

        # call report from UID model
        context["uid_report"] = uid_report(self.request.user)

        return context


# https://gist.github.com/cobusc/ea1d01611ef05dacb0f33307e292abf4
@login_required
def protected_view(request, path):
    """
    Redirect the request to the path used by nginx for protected media.
    """

    logger.debug("Received path %s for download" % (path))

    # test for submission ownership
    dirname = os.path.dirname(path)

    if dirname == 'data_source':
        # I got a submission. Get a submission belonging to owner or 404
        submission = get_object_or_404(
            Submission,
            owner=request.user,
            uploaded_file=path)

        logger.debug("Got submission %s" % (submission))

    # derive downloadable path. Applies to any protected file
    full_path = os.path.join(
        settings.PROTECTED_MEDIA_LOCATION_PREFIX, path
    )

    file_name = os.path.basename(path)

    # get file size using protected storage
    storage = ProtectedFileSystemStorage()
    file_size = storage.size(path)

    # force django to attach file in response
    # https://stackoverflow.com/a/1158750/4385116
    response = HttpResponse(content_type='application/force-download')
    response["X-Accel-Redirect"] = smart_str(full_path)
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        file_name)
    response['Content-Length'] = file_size

    return response
