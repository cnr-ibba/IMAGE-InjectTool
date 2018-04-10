#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 10 10:34:01 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""


class CryowebRouter(object):
    """
    A router to control all database operations on models in the
    cryoweb application.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read cryoweb models go to cryoweb db.
        """
        if model._meta.app_label == 'cryoweb':
            return 'cryoweb'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write cryoweb models go to cryoweb.
        """
        if model._meta.app_label == 'cryoweb':
            return 'cryoweb'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the cryoweb app is involved.
        """
        if obj1._meta.app_label == 'cryoweb' or \
           obj2._meta.app_label == 'cryoweb':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the cryoweb app only appears in the 'cryoweb'
        database.
        """
        if app_label == 'cryoweb':
            return db == 'cryoweb'
        return None
