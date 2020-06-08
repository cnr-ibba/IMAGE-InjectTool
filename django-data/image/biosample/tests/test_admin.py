#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 25 17:51:52 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from uid.tests.mixins import PersonMixinTestCase


class AdminTestCase(PersonMixinTestCase, TestCase):
    """With this module, I want to test custom admin classes. See:

    https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#admin-reverse-urls

    to have a list of admin views
    """

    fixtures = [
        'biosample/account',
        'biosample/managedteam',
        'biosample/orphansubmission',
        'biosample/submission',
        'biosample/submissiondata',
        'uid/animal',
        'uid/dictbreed',
        'uid/dictcountry',
        'uid/dictrole',
        'uid/dictsex',
        'uid/dictspecie',
        'uid/dictstage',
        'uid/dictuberon',
        'uid/ontology',
        'uid/organization',
        'uid/publication',
        'uid/sample',
        'uid/speciesynonym',
        'uid/submission',
        'uid/user'
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        # create an admin user
        User = get_user_model()
        User.objects.create_superuser(
            username='admin',
            password='test',
            email='admin@mail.com')

    def setUp(self):
        self.client = Client()
        self.client.login(username='admin', password='test')

    def check_response(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_submissionadmin(self):
        url = reverse('admin:biosample_submission_changelist')
        self.check_response(url)

    def test_submissiondataadmin(self):
        url = reverse('admin:biosample_submissiondata_changelist')
        self.check_response(url)

    def test_orphansubmissionadmin(self):
        url = reverse('admin:biosample_orphansubmission_changelist')
        self.check_response(url)
