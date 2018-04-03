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


class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(
            self.get_data(context),
            # https://stackoverflow.com/a/42418852
            json_dumps_params={'indent': 4},
            **response_kwargs
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


# Set custom method render_to_json_response as render_to_response
class JSONView(JSONResponseMixin, TemplateView):
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


# Set custom method render_to_json_response as render_to_response
class JSONDetailView(JSONResponseMixin, BaseDetailView):
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)
