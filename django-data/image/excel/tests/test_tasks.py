#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 11:51:09 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""


from django.test import TestCase

from common.tests import WebSocketMixin
from submissions.tests import ImportGenericTaskMixinTestCase

from .common import BaseExcelMixin
from ..tasks import ImportTemplateTask


class ImportTemplateTaskTest(
        ImportGenericTaskMixinTestCase, WebSocketMixin, BaseExcelMixin,
        TestCase):

    # custom values
    upload_method = "excel.tasks.upload_template"
    datasource_type = "Template"

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # setting task
        self.my_task = ImportTemplateTask()
