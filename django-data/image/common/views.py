#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 15:33:34 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin

# Get an instance of a logger
logger = logging.getLogger(__name__)


# a mixin to isolate user data
class OwnerMixin(LoginRequiredMixin):
    def get_queryset(self):
        qs = super(OwnerMixin, self).get_queryset()
        logger.debug("Checking '%s' ownership for user '%s'" % (
            self.request.path, self.request.user))
        return qs.filter(owner=self.request.user)
