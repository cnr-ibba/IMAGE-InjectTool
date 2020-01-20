#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 16:06:10 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import asyncio
import aiohttp

from yarl import URL
from multidict import MultiDict

from datetime import timedelta
from celery.utils.log import get_task_logger
from django.utils import timezone

from common.constants import COMPLETED, BIOSAMPLE_URL
from common.tasks import BaseTask, NotifyAdminTaskMixin, exclusive_task
from image.celery import app as celery_app

from ..helpers import get_manager_auth
from ..models import Submission

# Get an instance of a logger
logger = get_task_logger(__name__)

# defining constants
PAGE_SIZE = 20

PARAMS = MultiDict([
    ('size', PAGE_SIZE),
    ('filter', 'attr:project:IMAGE'),
    ])
HEADERS = {
        'Accept': 'application/hal+json',
    }


class CleanUpTask(NotifyAdminTaskMixin, BaseTask):
    """Perform biosample.models cleanup by selecting old completed submission
    and remove them from database"""

    name = "Clean biosample models"
    description = """Clean biosample models"""

    @exclusive_task(task_name="Clean biosample models", lock_id="CleanUpTask")
    def run(self):
        """
        This function is called when delay is called. It will acquire a lock
        in redis, so those tasks are mutually exclusive

        Returns:
            str: success if everything is ok. Different messages if task is
            already running or exception is caught"""

        logger.info("Clean biosample.database started")

        # get an interval starting from 7 days from now
        interval = timezone.now() - timedelta(days=7)

        # select all COMPLETED object older than interval
        qs = Submission.objects.filter(
            updated_at__lt=interval,
            status=COMPLETED)

        logger.info(
            "Deleting %s biosample.models.Submission objects" % qs.count())

        # delete all old objects
        qs.delete()

        # debug
        logger.info("Clean biosample.database completed")

        return "success"


async def fetch(session, url=BIOSAMPLE_URL, params=PARAMS):
    """Get a page from biosamples"""

    # define a URL with yarl
    url = URL(url)
    url = url.update_query(params)

    async with session.get(url, headers=HEADERS) as response:
        return await response.json()


async def get_samples(
        url=BIOSAMPLE_URL,
        params=PARAMS,
        managed_domains=[]):
    async with aiohttp.ClientSession() as session:
        data = await fetch(session, url, params)

        # get samples objects
        samples = data['_embedded']['samples']

        for sample in samples:
            # filter out unmanaged records
            if sample['domain'] not in managed_domains:
                logger.warning("Ignoring %s" % (sample['name']))
                continue

            # otherwise return to the caller the sample
            yield sample

        tasks = []

        # get pages
        totalPages = data['page']['totalPages']

        # generate new awaitable objects
        for page in range(1, totalPages):
            # get a new param object to edit
            my_params = params.copy()

            # edit a multidict object
            my_params.update(page=page)

            # track the new awaitable object
            tasks.append(fetch(session, url, my_params))

        # Run awaitable objects in the aws set concurrently.
        # Return an iterator of Future objects.
        for task in asyncio.as_completed(tasks):
            # read data
            data = await task

            # get samples objects
            samples = data['_embedded']['samples']

            for sample in samples:
                # filter out unmanaged records
                if sample['domain'] not in managed_domains:
                    logger.warning("Ignoring %s" % (sample['name']))
                    continue

                # otherwise return to the caller the sample
                yield sample


async def collect_samples():
    # I need an pyUSIrest.auth.Auth object to filter out records that don't
    # belong to me
    auth = get_manager_auth()
    managed_domains = auth.claims['domains']

    samples = []

    async for sample in get_samples(managed_domains=managed_domains):
        samples.append(sample)

    return samples


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(CleanUpTask)
