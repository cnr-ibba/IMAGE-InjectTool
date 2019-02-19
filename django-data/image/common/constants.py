#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 16:05:18 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from enum import Enum

# a constant for this module
OBO_URL = "http://purl.obolibrary.org/obo"


class ACCURACIES(Enum):
    missing = (0, 'missing geographic information')
    country = (1, 'country level')
    region = (2, 'region level')
    precise = (3, 'precise coordinates')
    unknown = (4, 'unknown accuracy level')

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
class CONFIDENCES(Enum):
    high = (0, 'High')
    good = (1, 'Good')
    medium = (2, 'Medium')
    low = (3, 'Low')
    curated = (4, 'Manually Curated')

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
# waiting: waiting to upload data (or process them!)
# loaded: data loaded into UID, can validate
# error: error in uploading data into UID or in submission
# ready: validated data ready for submission
# need_revision: validated data need checks before submission
# submitted: submitted to biosample
# completed: finalized submission with biosample id
class STATUSES(Enum):
    waiting = (0, 'Waiting')
    loaded = (1, 'Loaded')
    submitted = (2, 'Submitted')
    error = (3, 'Error')
    need_revision = (4, 'Need Revision')
    ready = (5, "Ready")
    completed = (6, "Completed")

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]


# a list of a valid statuse for names
NAME_STATUSES = [
    'loaded',
    'ready',
    'need_revision',
    'submitted',
    'completed'
]


# get statuses
WAITING = STATUSES.get_value('waiting')
LOADED = STATUSES.get_value('loaded')
ERROR = STATUSES.get_value('error')
READY = STATUSES.get_value('ready')
NEED_REVISION = STATUSES.get_value('need_revision')
SUBMITTED = STATUSES.get_value('submitted')
COMPLETED = STATUSES.get_value('completed')

# get accuracy levels
MISSING = ACCURACIES.get_value('missing')
UNKNOWN = ACCURACIES.get_value('unknown')
