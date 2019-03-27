#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 12:50:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from dateutil.relativedelta import relativedelta

from .constants import YEARS, MONTHS, DAYS


def image_timedelta(t1, t2):
    """A function to deal with image time intervals. Returns a number and
    time unit"""

    if t2 > t1:
        t1, t2 = t2, t1

    rdelta = relativedelta(t1, t2)

    if rdelta.years != 0:
        return rdelta.years, YEARS

    elif rdelta.months != 0:
        return rdelta.months, MONTHS

    else:
        return rdelta.days, DAYS
