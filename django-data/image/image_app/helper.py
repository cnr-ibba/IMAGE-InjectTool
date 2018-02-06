#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 12:41:05 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

Common functions in image_app

"""

import pandas as pd
from sqlalchemy import create_engine
from .models import Animal


class Database():
    """A base class for database connections"""

    def __init__(self):
        self.engine = None
        self.conn = None
        self.engine_uri = None

    def __del__(self):
        if self.conn is not None:
            self.conn.close()

    def get_engine(self):
        """Return an engine object"""

        if self.engine is None:
            # TODO: read parameters from file?
            self.engine = create_engine(self.engine_uri)

        return self.engine

    def get_connection(self, search_path=None):
        """Return a connection object and set search path"""

        if self.conn is None:
            # get engine and connect
            engine = self.get_engine()
            self.conn = engine.connect()

        if search_path is not None:
            self.conn.execute("SET search_path TO %s, public" % (
                    search_path))

        return self.conn


class CryowebDB(Database):
    """A class to deal with Cryoweb database instances. Define common methods
    useful in other parts of the code"""

    def __init__(self):
        super().__init__()

        self.engine_uri = (
                'postgresql://postgres:***REMOVED***@db:5432/imported_'
                'from_cryoweb')

    def has_data(self, search_path=None):
        """A method to test if database is filled or not. Returns True/False"""

        # get a connection
        conn = self.get_connection(search_path=search_path)

        num_animals = pd.read_sql_query(
                'select count(*) as num from animal',
                con=conn)

        num_animals = num_animals['num'].values[0]

        if num_animals > 0:
            return True

        else:
            return False


class ImageDB(Database):
    """A class to deal with Image database instances"""

    def __init__(self):
        super().__init__()

        self.engine_uri = (
                'postgresql://postgres:***REMOVED***@db:5432/image')

    def has_data(self, search_path=None):
        """A method to test if database is filled or not. Returns True/False"""

        # get a connection
        num_animals = Animal.objects.count()

        if num_animals > 0:
            return True

        else:
            return False
