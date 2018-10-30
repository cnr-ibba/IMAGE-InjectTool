#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 30 15:32:58 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.db.models.fields.files import FileField, ImageField

from .storage import ProtectedFileSystemStorage


# https://gist.github.com/cobusc/ea1d01611ef05dacb0f33307e292abf4
class ProtectedFileField(FileField):
    def __init__(self, *args, **kwargs):
        # override storage parameter
        kwargs["storage"] = ProtectedFileSystemStorage()

        super(ProtectedFileField, self).__init__(
            *args, **kwargs)


class ProtectedImageField(ImageField):
    def __init__(self, *args, **kwargs):
        # override storage parameter
        kwargs["storage"] = ProtectedFileSystemStorage()

        super(ProtectedFileField, self).__init__(
            *args, **kwargs)
