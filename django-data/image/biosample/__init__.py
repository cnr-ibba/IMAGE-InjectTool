#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 11:04:44 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

import pyUSIrest.settings

from common.constants import EBI_AAP_API_AUTH, BIOSAMPLE_API_ROOT

# Get an instance of a logger
logger = logging.getLogger(__name__)

# This code is executed every times this module or a part of this module is
# imported

# Ovveride pyUSIrest biosample urls, relying on common.constants
# declaring those values explicitely
logger.warning("Setting AAP API URL to: %s" % EBI_AAP_API_AUTH)

# Ovveride Auth.auth_url
pyUSIrest.settings.AUTH_URL = EBI_AAP_API_AUTH

logger.warning("Setting BIOSAMPLE API ROOT to: %s" % BIOSAMPLE_API_ROOT)

# Override Root api_root
pyUSIrest.settings.ROOT_URL = BIOSAMPLE_API_ROOT
