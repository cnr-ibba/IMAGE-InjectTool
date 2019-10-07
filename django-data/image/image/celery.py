#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 11 14:34:27 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os

from celery import Celery
from celery.signals import setup_logging

from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image.settings')

app = Celery('proj')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


# configure logging
# https://groups.google.com/forum/#!topic/celery-users/mhcwubJTTnw
@setup_logging.connect
def configure_logging(sender=None, **kwargs):
    import logging
    import logging.config
    logging.config.dictConfig(settings.LOGGING)
