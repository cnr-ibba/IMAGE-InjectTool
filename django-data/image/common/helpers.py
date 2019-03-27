#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 12:50:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from dateutil.relativedelta import relativedelta

from .constants import YEARS, MONTHS, DAYS

# Get an instance of a logger
logger = logging.getLogger(__name__)


def image_timedelta(t1, t2):
    """A function to deal with image time intervals. Returns a number and
    time unit"""

    if t2 > t1:
        logger.warning("t2>t1 ({0}, {1}) ignoring".format(t2, t1))
        return None, YEARS

    # check for meaningful intervald
    if t1.year == 1900 or t2.year == 1900:
        logger.warning("Ignoring one date ({0}, {1})".format(t2, t1))
        return None, YEARS

    rdelta = relativedelta(t1, t2)

    if rdelta.years != 0:
        return rdelta.years, YEARS

    elif rdelta.months != 0:
        return rdelta.months, MONTHS

    else:
        return rdelta.days, DAYS
