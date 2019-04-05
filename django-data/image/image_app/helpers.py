#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 12:41:05 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Common functions in image_app

"""

import datetime
import json
import logging
import os

from django.conf import settings

from decouple import AutoConfig

from common.constants import OBO_URL

# Get an instance of a logger
logger = logging.getLogger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


# Json encoder and decoder. Inspired from:
# https://gist.githubusercontent.com/abhinav-upadhyay/5300137/raw/71cd3b1660d0c1919bcfb4d39692030431623eea/DateTimeDecoder.py
# HINT: move to IMAGEEncoder?
# HINT: read GO from database?
class DateEncoder(json.JSONEncoder):
    """ Instead of letting the default encoder convert datetime to string,
        convert datetime objects into a dict, which can be decoded by the
        DateDecoder
    """

    def default(self, obj):
        # logger.debug(repr(obj))
        if isinstance(obj, datetime.date):
            return {
                'text': obj.isoformat(),
                'unit': "YYYY-MM-DD",
            }
        else:
            return json.JSONEncoder.default(self, obj)


class DateDecoder(json.JSONDecoder):
    def __init__(self, *args, **kargs):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object,
                                  *args, **kargs)

    def dict_to_object(self, d):
        """Call a different method when I found something like:
        {"text": "1991-07-26", "unit": "YYYY-MM-DD"}"""

        # return to caller if the keyword unit is not found
        if 'unit' not in d:
            return d

        # try to read datatime
        try:
            dateobj = datetime.datetime.strptime(d['text'], '%Y-%m-%d').date()
            return dateobj

        # if not, raise esception
        except Exception:
            return d


def format_attribute(value, terms=None, library_uri=OBO_URL, units=None):
    """Format a generic attribute into biosample dictionary"""

    if value is None:
        return None

    # pay attention to datetime objects
    if isinstance(value, datetime.date):
        value = str(value)

    # HINT: need I deal with multiple values?

    result = {}
    result["value"] = value

    if terms:
        result["terms"] = [{
            "url": "/".join([
                library_uri,
                terms])
        }]

    if units:
        result["units"] = units

    # return a list of dictionaries
    return [result]
