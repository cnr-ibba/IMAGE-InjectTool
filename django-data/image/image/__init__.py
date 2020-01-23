#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 11:36:25 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

__author__ = """Paolo Cozzi"""
__email__ = 'paolo.cozzi@ibba.cnr.it'
__version__ = '0.9.2'

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
