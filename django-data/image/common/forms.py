#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 20 16:56:36 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""


class RequestFormMixin():
    """remove self.request from kwargs to avoid errors"""

    # the request is now available, add it to the instance data
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(RequestFormMixin, self).__init__(*args, **kwargs)
