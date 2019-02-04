#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 12:34:22 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import logging

from django.views.generic import DetailView

from image_app.models import Animal
from common.views import OwnerMixin

# Get an instance of a logger
logger = logging.getLogger(__name__)


class DetailAnimalView(OwnerMixin, DetailView):
    model = Animal
    template_name = "animals/animal_detail.html"
