#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 10:54:09 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import json
import types
import asynctest

from aioresponses import aioresponses
from django.test import TestCase
from unittest.mock import patch, Mock

from common.constants import BIOSAMPLE_URL, SUBMITTED
from uid.models import Animal as UIDAnimal, Sample as UIDSample

from ..tasks.cleanup import check_samples, get_orphan_samples
from ..models import OrphanSample, ManagedTeam

from .common import generate_token, BioSamplesMixin

# get my path
dir_path = os.path.dirname(os.path.realpath(__file__))

# define data path
DATA_PATH = os.path.join(dir_path, "data")


with open(os.path.join(DATA_PATH, "page_0.json")) as handle:
    page0 = handle.read()

with open(os.path.join(DATA_PATH, "page_1.json")) as handle:
    page1 = handle.read()

with open(os.path.join(DATA_PATH, "issue_page1.json")) as handle:
    issue_page1 = handle.read()


class AsyncBioSamplesTestCase(asynctest.TestCase, TestCase):

    fixtures = [
        'biosample/managedteam',
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
        'uid/submission',
        'uid/user'
    ]

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        cls.mock_auth_patcher = patch('pyUSIrest.auth.requests.get')
        cls.mock_auth = cls.mock_auth_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_auth_patcher.stop()

        # calling base method
        super().tearDownClass()

    def setUp(self):
        # calling my base setup
        super().setUp()

        # well, updating data and set two biosample ids. Those are not
        # orphans
        animal = UIDAnimal.objects.get(pk=1)
        animal.biosample_id = "SAMEA6376980"
        animal.save()

        sample = UIDSample.objects.get(pk=1)
        sample.biosample_id = "SAMEA6376982"
        sample.save()

        # generate tocken
        self.mock_auth.return_value = Mock()
        self.mock_auth.return_value.text = generate_token()
        self.mock_auth.return_value.status_code = 200

    async def test_request(self) -> None:
        with aioresponses() as mocked:
            mocked.get(
                '{url}?filter=attr:project:IMAGE&size=20'.format(
                    url=BIOSAMPLE_URL),
                status=200,
                body=page0)
            mocked.get(
                '{url}?filter=attr:project:IMAGE&page=1&size=20'.format(
                    url=BIOSAMPLE_URL),
                status=200,
                body=page1)

            await check_samples()

            # get accessions
            reference = ['SAMEA6376991', 'SAMEA6376992']

            self.assertEqual(OrphanSample.objects.count(), 2)

            # check objects into UID
            for accession in reference:
                qs = OrphanSample.objects.filter(biosample_id=accession)
                self.assertTrue(qs.exists())

    async def test_request_with_issues(self) -> None:
        """Test a temporary issue with BioSamples reply"""

        with aioresponses() as mocked:
            mocked.get(
                '{url}?filter=attr:project:IMAGE&size=20'.format(
                    url=BIOSAMPLE_URL),
                status=200,
                body=page0)
            mocked.get(
                '{url}?filter=attr:project:IMAGE&page=1&size=20'.format(
                    url=BIOSAMPLE_URL),
                status=200,
                body=issue_page1)

            await check_samples()

            # no objects where tracked since issue in response
            self.assertEqual(OrphanSample.objects.count(), 0)


class PurgeOrphanSampleTestCase(BioSamplesMixin, TestCase):
    fixtures = [
        'biosample/managedteam',
        'biosample/orphansample',
        'uid/dictspecie',
    ]

    def test_purge_orphan_samples(self):
        """Test biosample data conversion"""

        with open(os.path.join(DATA_PATH, "SAMEA6376982.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        # call my method
        samples = get_orphan_samples()

        # teams is now a generator
        self.assertIsInstance(samples, types.GeneratorType)
        samples = list(samples)

        self.assertEqual(len(samples), 2)

        sample = samples[0]
        self.assertIsInstance(sample, dict)

        sample = samples[1]
        self.assertIsInstance(sample, dict)

        # read the team from data
        team = sample['team']
        self.assertIsInstance(team, ManagedTeam)

    def test_purge_orphan_samples_not_ready(self):
        """Test not ready orphan samples"""

        # Simulate a different status
        OrphanSample.objects.update(status=SUBMITTED)
        orphan_count = sum(1 for orphan in get_orphan_samples())

        self.assertEqual(orphan_count, 0)

    def test_purge_orphan_samples_ignore(self):
        """Test ignored orphan samples"""

        # Ignoring samples gives no object
        OrphanSample.objects.update(ignore=True)
        orphan_count = sum(1 for orphan in get_orphan_samples())

        self.assertEqual(orphan_count, 0)

    def test_purge_orphan_samples_removed(self):
        """Test removed orphan samples"""

        # Ignoring samples gives no object
        OrphanSample.objects.update(removed=True)
        orphan_count = sum(1 for orphan in get_orphan_samples())

        self.assertEqual(orphan_count, 0)
