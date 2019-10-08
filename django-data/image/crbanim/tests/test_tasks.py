#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 16:38:27 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase

from common.tests import WebSocketMixin
from submissions.tests import ImportGenericTaskMixinTestCase

from .common import BaseTestCase
from ..tasks import ImportCRBAnimTask


class ImportCRBAnimTaskTest(
        ImportGenericTaskMixinTestCase, WebSocketMixin, BaseTestCase,
        TestCase):

    # custom values
    upload_method = "crbanim.tasks.upload_crbanim"
    action = "crbanim import"

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # setting task
        self.my_task = ImportCRBAnimTask()
