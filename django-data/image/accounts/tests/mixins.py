#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mixins for accounts tests

"""

from unittest.mock import patch

from ..views import ResendActivationView, SignUpView


class OpenRegistrationMixin(object):
    """Registration is closed: re-open it just to test registration stuff.
    Place this mixin before TestCase in the base classes"""

    def setUp(self):
        # calling my base class setup
        super().setUp()

        for view in (SignUpView, ResendActivationView):
            patcher = patch.object(
                view, 'registration_allowed', return_value=True)
            patcher.start()
            self.addCleanup(patcher.stop)
