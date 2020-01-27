#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 16:06:10 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import asyncio
import aiohttp
import requests

from yarl import URL
from multidict import MultiDict

from datetime import timedelta
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.utils.dateparse import parse_date

from common.constants import COMPLETED, BIOSAMPLE_URL
from common.helpers import format_attribute
from common.tasks import BaseTask, NotifyAdminTaskMixin, exclusive_task
from image.celery import app as celery_app
from uid.models import Animal as UIDAnimal, Sample as UIDSample, DictSpecie

from ..helpers import get_manager_auth
from ..models import Submission, OrphanSample, ManagedTeam

# Get an instance of a logger
logger = get_task_logger(__name__)

# defining constants. Clean biosample database data after
CLEANUP_DAYS = 30

# this is the timedelta which I want to add to relaseDate to remove samples
RELEASE_TIMEDELTA = timedelta(days=365*1000)

# Setting page size for biosample requests
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

        # get an interval starting from now
        interval = timezone.now() - timedelta(days=CLEANUP_DAYS)

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


async def parse_samples_data(data, managed_domains):
    # get samples objects
    try:
        samples = data['_embedded']['samples']

        for sample in samples:
            # filter out unmanaged records
            if sample['domain'] not in managed_domains:
                logger.warning("Ignoring %s" % (sample['name']))
                continue

            # otherwise return to the caller the sample
            yield sample

    except KeyError as exc:
        # logger exception. With repr() the exception name is rendered
        logger.error(repr(exc))
        logger.warning("error while parsing samples")
        logger.warning(data)


async def get_samples(
        url=BIOSAMPLE_URL,
        params=PARAMS,
        managed_domains=[]):
    async with aiohttp.ClientSession() as session:
        data = await fetch(session, url, params)

        # process data and filter samples I own
        # https://stackoverflow.com/a/47378063
        async for sample in parse_samples_data(data, managed_domains):
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

            # process data and filter samples I own
            # https://stackoverflow.com/a/47378063
            async for sample in parse_samples_data(data, managed_domains):
                yield sample


async def check_samples():
    # I need an pyUSIrest.auth.Auth object to filter out records that don't
    # belong to me
    auth = get_manager_auth()
    managed_domains = auth.get_domains()

    async for sample in get_samples(managed_domains=managed_domains):
        check_orphan_sample(sample)


def check_orphan_sample(sample):
    animal_qs = UIDAnimal.objects.filter(
        biosample_id=sample['accession'])

    sample_qs = UIDSample.objects.filter(
        biosample_id=sample['accession'])

    if animal_qs.exists() or sample_qs.exists():
        logger.debug("Sample %s is tracked in UID" % (sample['accession']))

    else:
        # get a managed team
        team = ManagedTeam.objects.get(name=sample["domain"])

        # Create an orphan sample
        orphan, created = OrphanSample.objects.get_or_create(
            biosample_id=sample['accession'],
            name=sample['name'],
            team=team)

        if created:
            logger.warning("Add %s to orphan samples" % sample['accession'])


class SearchOrphanTask(NotifyAdminTaskMixin, BaseTask):
    """Search accross biosamples for objects not present in UID"""

    name = "Search Orphan BioSamples IDs"
    description = """Track BioSamples IDs not present in UID"""

    @exclusive_task(
        task_name=name, lock_id="SearchOrphanTask")
    def run(self):
        """
        This function is called when delay is called. It will acquire a lock
        in redis, so those tasks are mutually exclusive

        Returns:
            str: success if everything is ok. Different messages if task is
            already running or exception is caught"""

        logger.info("%s started" % (self.name))

        # create a loop object
        loop = asyncio.get_event_loop()

        # execute stuff
        try:
            loop.run_until_complete(check_samples())

        finally:
            # close loop
            loop.close()

        # debug
        logger.info("%s completed" % (self.name))

        return "success"


def purge_orphan_samples():
    """A function to remove objects from OrphanSample table"""

    with requests.Session() as session:
        for orphan_sample in OrphanSample.objects.filter(
                ignore=False, removed=False):

            # define the url I need to check
            url = "/".join([BIOSAMPLE_URL, orphan_sample.biosample_id])

            # read data from url
            response = session.get(url)
            data = response.json()

            # I need a new data dictionary to submit
            new_data = dict()

            # I suppose the accession exists, since I found this sample
            # using accession [biosample.id]
            new_data['accession'] = data.get(
                'accession', orphan_sample.biosample_id)

            new_data['alias'] = data['name']

            new_data['title'] = data['characteristics']['title'][0]['text']

            # this will be the most important attribute
            new_data['releaseDate'] = str(
                parse_date(data['releaseDate']) + RELEASE_TIMEDELTA)

            new_data['taxonId'] = data['taxId']

            # need to determine taxon as
            new_data['taxon'] = DictSpecie.objects.get(
                term__endswith=data['taxId']).label

            new_data['attributes'] = dict()

            # set project again
            new_data['attributes']["Project"] = format_attribute(
                value="IMAGE")

            # return new biosample data
            yield new_data


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(CleanUpTask)
celery_app.tasks.register(SearchOrphanTask)
