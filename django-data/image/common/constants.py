#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 16:05:18 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from enum import Enum

# a constant for this module
OBO_URL = "http://purl.obolibrary.org/obo"

# the biosample base url (set to definitive url)
BIOSAMPLE_URL = "https://wwwdev.ebi.ac.uk/biosamples/samples"


class EnumMixin():
    """Common methods for my Enum classes"""

    @classmethod
    def get_value(cls, member):
        """Get numerical representation of an Enum object"""

        return cls[member].value[0]

    @classmethod
    def get_value_display(cls, value):
        """Get the display value from a key"""

        if value is None:
            return None

        for el in cls:
            if el.value[0] == value:
                return el.value[1]

        raise KeyError("value %s not in %s" % (value, cls))

    @classmethod
    def get_value_by_desc(cls, value):
        """
        Get numerical representation of an Enum object by providing a
        description
        """

        if value is None:
            return None

        for el in cls:
            if el.value[1] == value:
                return el.value[0]

        raise KeyError("value '%s' not in '%s'" % (value, cls))


class ACCURACIES(EnumMixin, Enum):
    missing = (0, 'missing geographic information')
    country = (1, 'country level')
    region = (2, 'region level')
    precise = (3, 'precise coordinates')
    unknown = (4, 'unknown accuracy level')


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
class CONFIDENCES(EnumMixin, Enum):
    high = (0, 'High')
    good = (1, 'Good')
    medium = (2, 'Medium')
    low = (3, 'Low')
    curated = (4, 'Manually Curated')


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
# waiting: waiting to upload data (or process them!)
# loaded: data loaded into UID, can validate
# error: error in uploading data into UID or in submission
# ready: validated data ready for submission
# need_revision: validated data need checks before submission
# submitted: submitted to biosample
# completed: finalized submission with biosample id
class STATUSES(EnumMixin, Enum):
    waiting = (0, 'Waiting')
    loaded = (1, 'Loaded')
    submitted = (2, 'Submitted')
    error = (3, 'Error')
    need_revision = (4, 'Need Revision')
    ready = (5, "Ready")
    completed = (6, "Completed")


# 6.4.8 Better Model Choice Constants Using Enum (two scoops of django)
class DATA_TYPES(EnumMixin, Enum):
    cryoweb = (0, 'CryoWeb')
    template = (1, 'Template')
    crb_anim = (2, 'CRB-Anim')


# to deal with time units
class TIME_UNITS(EnumMixin, Enum):
    minutes = (0, "minutes")
    hours = (1, "hours")
    days = (2, "days")
    weeks = (3, "weeks")
    months = (4, "months")
    years = (5, "years")


# to deal with sample storage field
class SAMPLE_STORAGE(EnumMixin, Enum):
    ambient = (0, "ambient temperature")
    cut = (1, "cut slide")
    frozen80 = (2, "frozen, -80 degrees Celsius freezer")
    frozen20 = (3, "frozen, -20 degrees Celsius freezer")
    frozenliquid = (4, "frozen, liquid nitrogen")
    forzenvapor = (5, "frozen, vapor phase")
    paraffin = (6, "paraffin block")
    RNAlater = (7, "RNAlater, frozen -20 degrees Celsius")
    TRIzol = (8, "TRIzol, frozen")
    paraffinambient = (9, "paraffin block at ambient temperatures "
                          "(+15 to +30 degrees Celsius)")
    dried = (10, "freeze dried")
    frozen40 = (11, "frozen, -40 degrees Celsius freezer")


class SAMPLE_STORAGE_PROCESSING(EnumMixin, Enum):
    crio1 = (0, "cryopreservation in liquid nitrogen (dead tissue)")
    crio2 = (1, "cryopreservation in dry ice (dead tissue)")
    crio3 = (2, "cryopreservation of live cells in liquid nitrogen")
    crio4 = (3, "cryopreservation, other")
    formalin1 = (4, "formalin fixed, unbuffered")
    formalin2 = (5, "formalin fixed, buffered")
    formalin3 = (6, "formalin fixed and paraffin embedded")
    freeze1 = (7, "freeze dried (vaiable for reproduction)")
    freeze2 = (8, "freeze dried")


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
PRECISE = ACCURACIES.get_value('precise')

# get different data sources types
CRYOWEB_TYPE = DATA_TYPES.get_value('cryoweb')
TEMPLATE_TYPE = DATA_TYPES.get_value('template')
CRB_ANIM_TYPE = DATA_TYPES.get_value('crb_anim')

# get different confidence statuses
GOOD = CONFIDENCES.get_value('good')
CURATED = CONFIDENCES.get_value('curated')

# get time units
YEARS = TIME_UNITS.get_value('years')
MONTHS = TIME_UNITS.get_value('months')
DAYS = TIME_UNITS.get_value('days')

KNOWN_STATUSES = ['Error', 'Issues', 'Known', 'Pass', 'Warning']

VALIDATION_MESSAGES_ATTRIBUTES = [
    ['birth_location', 'birth_location_latitude', 'birth_location_longitude',
     'birth_location_accuracy'],
    ['collection_place', 'collection_place_latitude',
     'collection_place_longitude', 'collection_place_accuracy'],
    ['animal_age_at_collection_units', 'animal_age_at_collection'],
    ['preparation_interval_units', 'preparation_interval',
     'availability', 'protocol', 'storage', 'storage_processing'],
    ['organism_part', 'developmental_stage', 'physiological_stage'],
    ['sex', 'species'],
]

UNITS_VALIDATION_MESSAGES = [
    ".* for field .* is not in the valid units list .*",
    "One of .* need to be present for the field .*"
]

VALUES_VALIDATION_MESSAGES = [
    ".* of field .* is not in the valid values list .*",
]
