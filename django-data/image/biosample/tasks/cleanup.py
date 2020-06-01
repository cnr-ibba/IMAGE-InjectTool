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
from itertools import islice

from datetime import timedelta
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.utils.dateparse import parse_date

from common.constants import COMPLETED, BIOSAMPLE_URL, READY
from common.helpers import format_attribute, send_mail_to_admins
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
PAGE_SIZE = 500

BIOSAMPLE_PARAMS = MultiDict([
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


async def fetch_url(session, url=BIOSAMPLE_URL, params=BIOSAMPLE_PARAMS):
    """
    Fetch a generic url, read data as json and return a promise

    Parameters
    ----------
    session : aiohttp.ClientSession
        an async session object.
    url : str, optional
        the desidered url. The default is BIOSAMPLE_URL.
    params : MultiDict, optional
        Additional params for request. The default is BIOSAMPLE_PARAMS.

    Returns
    -------
    dict
        json content of the page

    """
    """"""

    # define a URL with yarl
    url = URL(url)
    url = url.update_query(params)

    logger.debug(url)

    async with session.get(url, headers=HEADERS) as response:
        try:
            return await response.json()

        except aiohttp.client_exceptions.ContentTypeError as exc:
            logger.error(repr(exc))
            logger.warning(
                "error while getting data from %s" % url)
            return {}


async def filter_managed_biosamples(data, managed_domains):
    """
    Parse data from a BioSample results page and yield samples managed
    by InjectTool users.

    Parameters
    ----------
    data : dict
        biosample data read from BIOSAMPLE_URL.
    managed_domains : list
        A list of AAP domains, as returned from
        :py:meth:`pyUSIrest.auth.Auth.get_domains`.

    Yields
    ------
    sample : dict
        a BioSample record.

    """
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


async def get_biosamples(
        url=BIOSAMPLE_URL,
        params=BIOSAMPLE_PARAMS,
        managed_domains=[]):
    """
    Get all records from BioSamples for the IMAGE project. Fecth Biosample
    once, determines how many pages to request and return only sample record
    managed by InjectTool

    Parameters
    ----------
    url : str, optional
        The desidered URL. The default is BIOSAMPLE_URL.
    params : MultiDict, optional
        Additional params for request. The default is BIOSAMPLE_PARAMS.
    managed_domains : list
        A list of AAP domains, as returned from
        :py:meth:`pyUSIrest.auth.Auth.get_domains`.

    Yields
    ------
    sample : dict
        a BioSample record.

    """
    # limiting the number of connections
    # https://docs.aiohttp.org/en/stable/client_advanced.html
    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)

    # https://stackoverflow.com/a/43857526
    async with aiohttp.ClientSession(connector=connector) as session:
        # get data for the first time to determine how many pages I have
        # to requests
        data = await fetch_url(session, url, params)

        # maybe the request had issues
        if data == {}:
            logger.debug("Got a result with no data")
            raise ConnectionError("Can't fetch biosamples for orphan samples")

        # process data and filter samples I own
        # https://stackoverflow.com/a/47378063
        async for sample in filter_managed_biosamples(data, managed_domains):
            # return a managed biosample record
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
            tasks.append(fetch_url(session, url, my_params))

        # Run awaitable objects in the aws set concurrently.
        # Return an iterator of Future objects.
        for task in asyncio.as_completed(tasks):
            # read data
            data = await task

            # maybe the request had issues
            if data == {}:
                logger.debug("Got a result with no data")
                continue

            # process data and filter samples I own
            # https://stackoverflow.com/a/47378063
            async for sample in filter_managed_biosamples(
                    data, managed_domains):
                yield sample


async def check_samples():
    """
    Get all records from BioSamples submitted by the InjectTool manager auth
    managed domains, and call check_orphan_sample for each of them

    Returns
    -------
    None.

    """
    # I need an pyUSIrest.auth.Auth object to filter out records that don't
    # belong to me
    auth = get_manager_auth()
    managed_domains = auth.get_domains()

    async for sample in get_biosamples(managed_domains=managed_domains):
        check_orphan_sample(sample)


def check_orphan_sample(sample):
    """
    Get a BioSample record and check if such BioSampleId is registered into
    InjectTool UID. If Such record is not present, create a new
    :py:class:`biosample.models.OrphanSample` record object in the BioSample
    orphan table

    Parameters
    ----------
    sample : dict
        a BioSample record.

    Returns
    -------
    None.

    """
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
            team=team,
            status=READY,
        )

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
        loop = asyncio.new_event_loop()

        # execute stuff
        try:
            loop.run_until_complete(check_samples())

        finally:
            # close loop
            loop.close()

        # Ok count orphan samples
        orphan_count = sum(1 for orphan in get_orphan_samples())

        if orphan_count > 0:
            email_subject = "Some entries in BioSamples are orphan"
            email_message = (
                "There are %s biosample ids which are not managed by "
                "InjectTool" % orphan_count)

            logger.warning(email_message)

            # Notify admins if I have orphan samples
            send_mail_to_admins(email_subject, email_message)

        # debug
        logger.info("%s completed" % (self.name))

        return "success"


def get_orphan_samples(limit=None):
    """
    Iterate for all BioSample orphaned records which are not yet removed and
    are tracked for removal, get minimal data from BioSample and return a
    dictionary which can be used to patch a BioSample id with a new
    BioSample submission in order to remove a BioSamples record
    (publish the BioSample record after 1000 years from Now).

    Yields
    ------
    new_data : dict
        payload to submit to BioSample in order to remove a BioSamples record.
    """

    with requests.Session() as session:
        # get all biosamples candidate for a removal. Pay attention that
        # could be removed from different users
        qs = OrphanSample.objects.filter(
            ignore=False,
            removed=False,
            status=READY
        ).order_by('team__name', 'id')

        if limit:
            qs = islice(qs, limit)

        for orphan_sample in qs:
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

            new_data['description'] = "Removed by InjectTool"

            # set project again
            new_data['attributes']["Project"] = format_attribute(
                value="IMAGE")

            # return new biosample data
            yield {
                'data': new_data,
                'team': orphan_sample.team,
                'sample': orphan_sample,
            }


# register explicitly tasks
# https://github.com/celery/celery/issues/3744#issuecomment-271366923
celery_app.tasks.register(CleanUpTask)
celery_app.tasks.register(SearchOrphanTask)
