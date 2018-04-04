#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 11:20:58 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

# https://docs.djangoproject.com/en/1.11/topics/class-based-views/mixins/#more-than-just-html
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView


# HINT: move to a mixin module?
class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """

        if 'json_dumps_params' not in response_kwargs:
            response_kwargs['json_dumps_params'] = {}

        # https://stackoverflow.com/a/42418852
        response_kwargs['json_dumps_params']['indent'] = 4

        return JsonResponse(
            self.get_data(context),
            **response_kwargs,
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return context


class BioSampleMixin(JSONResponseMixin):
    """A mixin to deal with context with biosample tag"""

    def get_data(self, context):
        """Override default get data object"""

        return context["biosample"]


# Set custom method render_to_json_response as render_to_response. TemplateView
# doesn't query the database, it renders a template
class JSONView(JSONResponseMixin, TemplateView):
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


# Set custom method render_to_json_response as render_to_response.
# BaseDetailView queries databases using pk and model attribute (default)
class JSONDetailView(JSONResponseMixin, BaseDetailView):
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


class JSONListView(JSONResponseMixin, BaseListView):
    def render_to_response(self, context, **response_kwargs):
        # override safe parameter to dump a list of dictionaries
        response_kwargs["safe"] = False
        return self.render_to_json_response(context, **response_kwargs)


# Inherits get_data from BioSampleMixin, and render_to_response from
# JSONView
class BioSampleView(BioSampleMixin, JSONView):
    pass


# Inherits get_data from BioSampleMixin, and render_to_response from
# JSONDetailView
class BioSampleDetailView(BioSampleMixin, JSONDetailView):
    pass


# a biosample view for a list
class BioSampleListView(BioSampleMixin, JSONListView):
    pass
