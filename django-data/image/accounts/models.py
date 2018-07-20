#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 13:35:27 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import string
import hashlib
import logging

from django.core.exceptions import MultipleObjectsReturned
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string

from registration.models import RegistrationProfile, RegistrationManager


# Get an instance of a logger
logger = logging.getLogger(__name__)


class MyRegistrationManager(RegistrationManager):
    def resend_activation_mail(self, email, site, request=None):
        """
        Resets activation key for the user and resends activation email. If
        activation_key is expired, generate a new key
        """

        try:
            profile = self.get(user__email__iexact=email)
        except ObjectDoesNotExist:
            return False
        except MultipleObjectsReturned:
            return False

        if profile.activated:
            return False

        profile.create_new_activation_key()
        profile.send_activation_email(site, request)

        return True


# Sometimes you only want to change the Python behavior of a model – perhaps to
# change the default manager, or add a new method. This is what proxy model
# inheritance is for: creating a proxy for the original model. You can create,
# delete and update instances of the proxy model and all the data will be
# saved as if you were using the original (non-proxied) model. The difference
# is that you can change things like the default model ordering or the
# default manager in the proxy, without having to alter the original.
class MyRegistrationProfile(RegistrationProfile):
    objects = MyRegistrationManager()

    class Meta:
        proxy = True

    def create_new_activation_key(self, save=True):
        """
        Create a new activation key for the user. If the old one is still valid
        return it
        """

        if not self.activation_key or self.activation_key_expired():
            logger.debug("Generating a new activation key")

            random_string = get_random_string(
                length=32, allowed_chars=string.printable)
            self.activation_key = hashlib.sha1(
                random_string.encode('utf-8')).hexdigest()

            if save:
                self.save()

        else:
            logger.debug("Returning the already generated activation key")

        return self.activation_key
