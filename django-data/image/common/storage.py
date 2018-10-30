#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 30 15:28:14 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.core.files.storage import FileSystemStorage
from django.utils.functional import cached_property

from django.conf import settings


class ProtectedFileSystemStorage(FileSystemStorage):
    @cached_property
    def base_location(self):
        return self._value_or_setting(
            self._location, settings.PROTECTED_MEDIA_ROOT)

    @cached_property
    def base_url(self):
        if self._base_url is not None and not self._base_url.endswith('/'):
            self._base_url += '/'
        return self._value_or_setting(
            self._base_url, settings.PROTECTED_MEDIA_URL)
