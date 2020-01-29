#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 19 16:51:05 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.test import TestCase
from django.template import Template, Context

from common.constants import (
    WAITING, LOADED, ERROR, READY, NEED_REVISION, SUBMITTED, COMPLETED)
from uid.models import Submission, User


class CommonTestCase():
    """Does the common stuff when testing cases are run"""

    fixtures = [
        "uid/user",
        "uid/dictcountry",
        "uid/dictrole",
        "uid/organization",
        "uid/submission"
    ]

    def setUp(self):
        self.submission = Submission.objects.get(pk=1)

    def render_status(self, status):
        self.submission.status = status
        self.submission.save()

        return self.TEMPLATE.render(
            Context({'submission': self.submission}))


class CanEditTest(CommonTestCase, TestCase):
    """Test if I can edit data against different submission statuses"""

    TEMPLATE = Template(
        "{% load submissions_tags %}{% can_edit submission %}"
    )

    def test_is_waiting(self):
        rendered = self.render_status(WAITING)
        self.assertEqual(rendered, "False")

    def test_is_loaded(self):
        rendered = self.render_status(LOADED)
        self.assertEqual(rendered, "True")

    def test_is_error(self):
        rendered = self.render_status(ERROR)
        self.assertEqual(rendered, "True")

    def test_is_ready(self):
        rendered = self.render_status(READY)
        self.assertEqual(rendered, "True")

    def test_need_revision(self):
        rendered = self.render_status(NEED_REVISION)
        self.assertEqual(rendered, "True")

    def test_is_submitted(self):
        rendered = self.render_status(SUBMITTED)
        self.assertEqual(rendered, "False")

    def test_is_completed(self):
        rendered = self.render_status(COMPLETED)
        self.assertEqual(rendered, "True")


class CanValidateTest(CommonTestCase, TestCase):
    """Test if I can validate data against different submission statuses"""

    TEMPLATE = Template(
        "{% load submissions_tags %}{% can_validate submission %}"
    )

    def test_is_waiting(self):
        rendered = self.render_status(WAITING)
        self.assertEqual(rendered, "False")

    def test_is_loaded(self):
        rendered = self.render_status(LOADED)
        self.assertEqual(rendered, "True")

    def test_is_error(self):
        rendered = self.render_status(ERROR)
        self.assertEqual(rendered, "False")

    def test_is_ready(self):
        rendered = self.render_status(READY)
        self.assertEqual(rendered, "False")

    def test_need_revision(self):
        rendered = self.render_status(NEED_REVISION)
        self.assertEqual(rendered, "True")

    def test_is_submitted(self):
        rendered = self.render_status(SUBMITTED)
        self.assertEqual(rendered, "False")

    def test_is_completed(self):
        rendered = self.render_status(COMPLETED)
        self.assertEqual(rendered, "False")


class CanSubmitTest(CommonTestCase, TestCase):
    """Test if I can submit data against different submission statuses"""

    TEMPLATE = Template(
        "{% load submissions_tags %}{% can_submit submission %}"
    )

    def test_is_waiting(self):
        rendered = self.render_status(WAITING)
        self.assertEqual(rendered, "False")

    def test_is_loaded(self):
        rendered = self.render_status(LOADED)
        self.assertEqual(rendered, "False")

    def test_is_error(self):
        rendered = self.render_status(ERROR)
        self.assertEqual(rendered, "False")

    def test_is_ready(self):
        rendered = self.render_status(READY)
        self.assertEqual(rendered, "True")

    def test_need_revision(self):
        rendered = self.render_status(NEED_REVISION)
        self.assertEqual(rendered, "False")

    def test_is_submitted(self):
        rendered = self.render_status(SUBMITTED)
        self.assertEqual(rendered, "False")

    def test_is_completed(self):
        rendered = self.render_status(COMPLETED)
        self.assertEqual(rendered, "False")


class HaveSubmissionTest(CommonTestCase, TestCase):
    TEMPLATE = Template(
        "{% load submissions_tags %}{% have_submission user %}"
    )

    def setUp(self):
        # create a test user
        super().setUp()

        self.user = User.objects.get(pk=1)

    def test_have_submission(self):
        rendered = self.TEMPLATE.render(
            Context({'user': self.user}))
        self.assertEqual(rendered, "True")

    def test_ownership(self):
        """Check a user with no submissions"""

        user = User.objects.get(pk=2)

        rendered = self.TEMPLATE.render(
            Context({'user': user}))
        self.assertEqual(rendered, "False")
