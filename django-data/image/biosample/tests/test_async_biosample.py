#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 10:54:09 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import asynctest

from aioresponses import aioresponses

from common.constants import BIOSAMPLE_URL

from ..tasks.cleanup import collect_samples

# get my path
dir_path = os.path.dirname(os.path.realpath(__file__))

# define data path
DATA_PATH = os.path.join(dir_path, "data")


with open(os.path.join(DATA_PATH, "page_0.json")) as handle:
    page0 = handle.read()

with open(os.path.join(DATA_PATH, "page_1.json")) as handle:
    page1 = handle.read()


class AsyncBioSamplesTestCase(asynctest.TestCase):
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

            samples = await collect_samples()

            # get accessions
            accessions = [sample['accession'] for sample in samples]
            accessions.sort()

            reference = [
                'SAMEA6376980',
                'SAMEA6376982',
                'SAMEA6376991',
                'SAMEA6376992']

            self.assertEqual(accessions, reference)
