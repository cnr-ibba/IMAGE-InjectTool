#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 10:54:09 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import json
import time
import types
import asynctest

from aioresponses import aioresponses
from aiohttp.client_exceptions import ServerDisconnectedError
from unittest.mock import patch, Mock

from django.test import TestCase
from django.utils import timezone

from common.constants import SUBMITTED, READY, COMPLETED
from uid.models import Animal as UIDAnimal, Sample as UIDSample

from ..tasks.cleanup import (
    check_samples, get_orphan_samples, PAGE_SIZE, BIOSAMPLE_ACCESSION_ENDPOINT,
    BIOSAMPLE_SAMPLE_ENDPOINT)
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

mocked_accessions = {}

for accession in ["SAMEA6376679", "SAMEA6376682", "SAMEA6376980",
                  "SAMEA6376982", "SAMEA6376991", "SAMEA6376992"]:
    with open(os.path.join(DATA_PATH, f"{accession}.json")) as handle:
        mocked_accessions[accession] = handle.read()


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

    async def check_samples(self):
        with aioresponses() as mocked:
            mocked.get(
                '{url}?filter=attr:project:IMAGE&size={size}'.format(
                    url=BIOSAMPLE_ACCESSION_ENDPOINT, size=PAGE_SIZE),
                status=200,
                body=page0)
            mocked.get(
                '{url}?filter=attr:project:IMAGE&page=1&size={size}'.format(
                    url=BIOSAMPLE_ACCESSION_ENDPOINT, size=PAGE_SIZE),
                status=200,
                body=page1)
            for accession, body in mocked_accessions.items():
                mocked.get(
                    '{url}/{accession}'.format(
                        url=BIOSAMPLE_SAMPLE_ENDPOINT, accession=accession),
                    status=200,
                    body=body)

            await check_samples()

    async def test_request(self) -> None:
        await self.check_samples()

        # get accessions
        reference = ['SAMEA6376991', 'SAMEA6376992']

        self.assertEqual(OrphanSample.objects.count(), 2)

        # check objects into UID
        for accession in reference:
            orphan = OrphanSample.objects.get(biosample_id=accession)
            orphan.status = READY

    async def test_request_with_issues(self) -> None:
        """Test a temporary issue with BioSamples reply"""

        with aioresponses() as mocked:
            mocked.get(
                '{url}?filter=attr:project:IMAGE&size={size}'.format(
                    url=BIOSAMPLE_ACCESSION_ENDPOINT, size=PAGE_SIZE),
                status=200,
                body=page0)
            mocked.get(
                '{url}?filter=attr:project:IMAGE&page=1&size={size}'.format(
                    url=BIOSAMPLE_ACCESSION_ENDPOINT, size=PAGE_SIZE),
                status=200,
                body=issue_page1)
            for accession, body in mocked_accessions.items():
                mocked.get(
                    '{url}/{accession}'.format(
                        url=BIOSAMPLE_SAMPLE_ENDPOINT, accession=accession),
                    status=200,
                    body=body)

            await check_samples()

        # no objects where tracked since issue in response
        self.assertEqual(OrphanSample.objects.count(), 0)

    async def test_request_with_html(self) -> None:
        """Test a not JSON response (HTML)"""

        with aioresponses() as mocked:
            mocked.get(
                '{url}?filter=attr:project:IMAGE&size={size}'.format(
                    url=BIOSAMPLE_ACCESSION_ENDPOINT, size=PAGE_SIZE),
                status=200,
                body=page0)
            mocked.get(
                '{url}?filter=attr:project:IMAGE&page=1&size={size}'.format(
                    url=BIOSAMPLE_ACCESSION_ENDPOINT, size=PAGE_SIZE),
                status=200,
                headers={'Content-type': 'text/html'},
                body="<html>Not a JSON</html>")
            for accession, body in mocked_accessions.items():
                mocked.get(
                    '{url}/{accession}'.format(
                        url=BIOSAMPLE_SAMPLE_ENDPOINT, accession=accession),
                    status=200,
                    body=body)

            await check_samples()

        # no objects where tracked since issue in response
        self.assertEqual(OrphanSample.objects.count(), 0)

    async def test_biosamples_down(self) -> None:
        """Test a not JSON response (HTML): BioSamples down"""

        with aioresponses() as mocked:
            mocked.get(
                '{url}?filter=attr:project:IMAGE&size={size}'.format(
                    url=BIOSAMPLE_ACCESSION_ENDPOINT, size=PAGE_SIZE),
                status=200,
                headers={'Content-type': 'text/html'},
                body="<html>Not a JSON</html>")
            mocked.get(
                '{url}?filter=attr:project:IMAGE&page=1&size={size}'.format(
                    url=BIOSAMPLE_ACCESSION_ENDPOINT, size=PAGE_SIZE),
                status=200,
                headers={'Content-type': 'text/html'},
                body="<html>Not a JSON</html>")

            with self.assertRaises(ConnectionError):
                await check_samples()

        # no objects where tracked since issue in response
        self.assertEqual(OrphanSample.objects.count(), 0)

    async def test_server_lost(self) -> None:
        """Test server disconnect error"""

        with aioresponses() as mocked:
            mocked.get(
                '{url}?filter=attr:project:IMAGE&size={size}'.format(
                    url=BIOSAMPLE_ACCESSION_ENDPOINT, size=PAGE_SIZE),
                exception=ServerDisconnectedError()
            )

            with self.assertRaises(ConnectionError):
                await check_samples()

        # no objects where tracked since issue in response
        self.assertEqual(OrphanSample.objects.count(), 0)

    async def test_already_removed_samples(self) -> None:
        """Test check samples with entries in database"""

        # create items into database. get team first
        team = ManagedTeam.objects.get(pk=1)

        sample1 = OrphanSample.objects.create(
            biosample_id='SAMEA6376991',
            name="IMAGEA000005610",
            team=team,
            status=SUBMITTED,
        )

        sample2 = OrphanSample.objects.create(
            biosample_id='SAMEA6376992',
            name="IMAGEA000005607",
            team=team,
            status=COMPLETED,
            removed=True,
            removed_at=timezone.now()
        )

        await self.check_samples()

        # test: there are the same samples in database
        self.assertEqual(OrphanSample.objects.count(), 2)

        # no changes in statuses
        self.assertEqual(sample1.status, SUBMITTED)
        self.assertEqual(sample2.status, COMPLETED)


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

    def test_purge_orphan_samples_with_limit(self):
        """Test get orphan samples with limits"""

        orphan_count = sum(1 for orphan in get_orphan_samples(limit=1))
        self.assertEqual(orphan_count, 1)

    def test_purge_orphan_private(self):
        """Test no access to a BioSamples id (already removed?)"""

        data = {
            'timestamp': int(time.time() * 1000),
            'status': 403,
            'error': 'Forbidden',
            'exception': (
                'uk.ac.ebi.biosamples.service.'
                'BioSamplesAapService$SampleNotAccessibleException'),
            'message': (
                'This sample is private and not available for browsing. '
                'If you think this is an error and/or you should have access '
                'please contact the BioSamples Helpdesk at biosamples@'
                'ebi.ac.uk'),
            'path': '/biosamples/samples/SAMEA6376982'
        }

        # override mock object
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 403

        orphan_count = sum(1 for orphan in get_orphan_samples(limit=1))
        self.assertEqual(orphan_count, 0)
