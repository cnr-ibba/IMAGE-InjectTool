#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 14:40:44 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Here I will set all the tests.mixins I want to export outside common.tests

"""

from .mixins import (
    DataSourceMixinTestCase, FormMixinTestCase, GeneralMixinTestCase,
    InvalidFormMixinTestCase, LoginMixinTestCase, MessageMixinTestCase,
    OwnerMixinTestCase, PersonMixinTestCase, StatusMixinTestCase)

__all__ = [
    "DataSourceMixinTestCase", "FormMixinTestCase", "GeneralMixinTestCase",
    "InvalidFormMixinTestCase", "LoginMixinTestCase", "MessageMixinTestCase",
    "OwnerMixinTestCase", "PersonMixinTestCase", "StatusMixinTestCase"]
