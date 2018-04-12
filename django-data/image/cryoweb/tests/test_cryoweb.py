#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  9 16:58:01 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>
"""

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.messages import get_messages

from image_app.models import User


class FillUIDTestClass(TestCase):
    # import this file and populate database once
    fixtures = ["cryoweb.json", "datasource.json"]

    # By default, fixtures are only loaded into the default database. If you
    # are using multiple databases and set multi_db=True, fixtures will be
    # loaded into all databases.
    multi_db = True

    # https://docs.djangoproject.com/en/1.11/topics/testing/advanced/#example
    def setUp(self):
        """Connect to client"""
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='test', email='test@test.com', password='test')

        self.client = Client()
        self.client.login(username='test', password='test')

    def test_cryoweb_already_imported(self):
        # Create an instance of a GET request.
        # request = self.factory.get(reverse('image_app:upload_cryoweb'))

        # Recall that middleware are not supported. You can simulate a
        # logged-in user by setting request.user manually.
        # request.user = self.user

        # Test upload_cryoweb() as if it were deployed at
        # reverse('image_app:upload_cryoweb')
        # response = upload_cryoweb(request)

        # same thing, but with a client request
        response = self.client.get(
                reverse('image_app:upload_cryoweb'))

        # each element is an instance
        # of django.contrib.messages.storage.base.Message
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        for message in all_messages:
            self.assertEqual(message.tags, "warning")
            self.assertEqual(
                    message.message,
                    "cryoweb mirror database has data. Ignoring data load")
