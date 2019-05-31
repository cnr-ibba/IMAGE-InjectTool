#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 12:50:16 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging
import websockets
import time

from dateutil.relativedelta import relativedelta

from django.contrib.admin.utils import NestedObjects
from django.db import DEFAULT_DB_ALIAS
from django.utils.text import capfirst
from django.utils.encoding import force_text

from .constants import YEARS, MONTHS, DAYS

# Get an instance of a logger
logger = logging.getLogger(__name__)


def image_timedelta(t1, t2):
    """A function to deal with image time intervals. Returns a number and
    time unit"""

    if t1 is None or t2 is None:
        logger.warning("One date is NULL ({0}, {1}) ignoring".format(t2, t1))
        return None, YEARS

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


# https://stackoverflow.com/a/39533619/4385116
# inspired django.contrib.admin.utils.get_deleted_objects, this function
# tries to determine all related objects starting from a provied one
# HINT: similar function at https://gist.github.com/nealtodd/4594575
def get_deleted_objects(objs, db_alias=DEFAULT_DB_ALIAS):
    # NestedObjects is an imporovement of django.db.models.deletion.Collector
    collector = NestedObjects(using=db_alias)
    collector.collect(objs)

    def format_callback(obj):
        opts = obj._meta
        no_edit_link = '%s: %s' % (capfirst(opts.verbose_name),
                                   force_text(obj))
        return no_edit_link

    to_delete = collector.nested(format_callback)
    protected = [format_callback(obj) for obj in collector.protected]
    model_count = {
        model._meta.verbose_name_plural:
            len(objs) for model, objs in collector.model_objs.items()}

    return to_delete, model_count, protected


async def send_message_to_websocket(message, pk):
    """
    Function will create websocket object and send message to django-channels
    Args:
        message (str): message to send to websocket
        pk (str): primary key of submission
    """
    # Need to have it here as in case with small test data message sent to
    # websocket will overcome response from server
    time.sleep(3)
    async with websockets.connect(
            'ws://asgi:8001/image/ws/submissions/{}/'.format(pk)) as websocket:
        await websocket.send(message)
