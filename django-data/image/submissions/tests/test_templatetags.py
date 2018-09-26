#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 19 16:51:05 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase
from django.template import Template, Context

from image_app.models import Submission


class CommonTestCase():
    """Does the common stuff when testing cases are run"""

    fixtures = [
        "submissions/user",
        "submissions/dictcountry",
        "submissions/dictrole",
        "submissions/organization",
        "submissions/submission"
    ]

    def setUp(self):
        self.submission = Submission.objects.get(pk=1)

    def test_tag_not_present(self):
        self.submission.status = Submission.STATUSES.get_value('loaded')
        self.submission.save()

        rendered = self.TEMPLATE.render(
            Context({'submission': self.submission}))

        self.assertEqual(rendered, "False")


class IsWaitingTest(CommonTestCase, TestCase):
    TEMPLATE = Template(
        "{% load submissions_tags %}{% is_waiting submission %}"
    )

    def test_is_waiting(self):
        rendered = self.TEMPLATE.render(
            Context({'submission': self.submission}))

        self.assertEqual(rendered, "True")


class HasErrorsTest(CommonTestCase, TestCase):
    TEMPLATE = Template(
        "{% load submissions_tags %}{% has_errors submission %}"
    )

    def test_has_error(self):
        self.submission.status = Submission.STATUSES.get_value('error')
        self.submission.save()

        rendered = self.TEMPLATE.render(
            Context({'submission': self.submission}))

        self.assertEqual(rendered, "True")
