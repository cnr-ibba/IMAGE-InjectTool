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

import pandas as pd
from django.conf import settings
from sqlalchemy import create_engine

from decouple import AutoConfig

from .constants import OBO_URL

# Get an instance of a logger
logger = logging.getLogger(__name__)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


# TODO: remove this class
class Database(object):
    """A base class for database connections"""

    def __init__(self):
        self.engine = None
        self.conn = None
        self.engine_uri = None

    def __del__(self):
        logger.debug("self.conn is %s" % self.conn)

        if self.conn is not None:
            logger.debug("Closing connection")
            self.conn.close()

    def get_engine(self):
        """Return an engine object"""

        if self.engine is None:
            # TODO: read parameters from file?
            self.engine = create_engine(self.engine_uri)

        return self.engine

    def get_connection(self, search_path=None):
        """Return a connection object and set search path"""

        if self.conn is None:
            # get engine and connect
            engine = self.get_engine()
            self.conn = engine.connect()

        if search_path is not None:
            self.conn.execute("SET search_path TO %s, public" % (
                    search_path))

        return self.conn


# TODO: remove this class and fix truncate_image_tables
class ImageDB(Database):
    """A class to deal with Image database instances"""

    def __init__(self):
        super().__init__()

        self.engine_uri = (
            'postgresql://{user}:{password}@db:5432/image'.format(
                user=config('IMAGE_USER'),
                password=config('IMAGE_PASSWORD')))

    # TODO: remove this: check using django ORM
    def has_data(self, search_path=None):
        """A method to test if database is filled or not. Returns True/False"""

        # get a connection
        conn = self.get_connection(search_path=search_path)

        num_animals = pd.read_sql_query(
            'select count(*) as num from image_app_animal',
            con=conn)

        num_animals = num_animals['num'].values[0]

        if num_animals > 0:
            return True

        else:
            return False


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


def format_attribute(value, terms=None, units=None):
    """Format a generic attribute into biosample dictionary"""

    if value is None:
        return None

    # HINT: need I deal with multiple values?

    result = {}
    result["value"] = value

    if terms:
        result["terms"] = [{
            "url": "/".join([
                OBO_URL,
                terms])
        }]

    if units:
        result["units"] = units

    # return a list of dictionaries
    return [result]
