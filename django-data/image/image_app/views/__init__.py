#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 10:38:00 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Importing submodules as will be by loading views.py

"""

from .image import (
    IndexView, AboutView, DashBoardView, SummaryView, protected_view)

from .export import (
    SampleJSON, SampleListJSON, AnimalJSON, AnimalListJSON, BioSampleJSON,
    BioSampleListJSON)

__all__ = [
    'SampleJSON', 'SampleListJSON', 'AnimalJSON',
    'AnimalListJSON', 'BioSampleJSON', 'BioSampleListJSON', 'IndexView',
    'AboutView', 'DashBoardView', 'SummaryView', 'protected_view']
