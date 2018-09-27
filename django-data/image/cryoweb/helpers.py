#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 14 10:28:39 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import shlex
import logging
import subprocess

from decouple import AutoConfig

from django.conf import settings

from image_app.models import Submission
from cryoweb.models import VBreedSpecies, db_has_data as cryoweb_has_data
from language.models import SpecieSynonim

# Get an instance of a logger
logger = logging.getLogger(__name__)


# a function to detect if cryoweb species have synonims or not
def check_species(language):
    """Check specie for a language, ie: check_species(language='Germany').
    Language is image_app.models.DictCountry.label"""

    # get all species using view
    species = VBreedSpecies.get_all_species()

    # for logging purposes
    database_name = settings.DATABASES['cryoweb']['NAME']

    # debug
    logger.debug("Got %s species from %s" % (species, database_name))

    # get a queryset for each
    synonims = SpecieSynonim.objects.filter(
        word__in=species, language__label=language)

    # HINT: is this state useful?
    # check that numbers are equal
    if len(species) == synonims.count():
        logger.debug("Each species has a synonim in %s language" % (language))
        return True

    elif len(species) > synonims.count():
        logger.warning(
            "Some species haven't a synonim for language: %s!" % (language))
        logger.debug("Following terms lack of synonim:")
        for specie in species:
            if not SpecieSynonim.objects.filter(
                    word=specie, language__label=language).exists():
                logger.debug(specie)
        return False

    # may I see this case? For instance when filling synonims?
    else:
        raise NotImplementedError("Not implemented")


# A class to deal with cryoweb import errors
class CryoWebImportError(Exception):
    pass


def upload_cryoweb(submission_id):
    """Imports backup into the cryoweb db

    This function uses the container's installation of psql to import a backup
    file into the "cryoweb" database. The imported backup file is
    the last inserted into the image's table image_app_submission.

    :submission_id: the submission primary key
    """

    # define some useful variables
    database_name = settings.DATABASES['cryoweb']['NAME']

    # define a decouple config object
    config_dir = os.path.join(settings.BASE_DIR, 'image')
    config = AutoConfig(search_path=config_dir)

    # get a submission object
    submission = Submission.objects.get(pk=submission_id)

    # debug
    logger.debug("Got Submission %s" % (submission))

    # If cryoweb has data, update submission message and return exception:
    # maybe another process is running or there is another type of problem
    if cryoweb_has_data():
        logger.error("Cryoweb has data!")

        # update submission status
        submission.status = Submission.STATUSES.get_value('error')
        submission.message = "Cryoweb has data"
        submission.save()

        raise CryoWebImportError("Cryoweb has data!")

    # this is the full path in docker container
    fullpath = submission.uploaded_file.file

    # get a string and quote fullpath
    fullpath = shlex.quote(str(fullpath))

    # define command line
    cmd_line = "/usr/bin/psql -U {user} -h db {database}".format(
        database=database_name, user='cryoweb_insert_only')

    cmds = shlex.split(cmd_line)

    logger.debug("Executing: %s" % " ".join(cmds))

    try:
        result = subprocess.run(
            cmds,
            stdin=open(fullpath),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            env={'PGPASSWORD': config('CRYOWEB_INSERT_ONLY_PW')},
            encoding='utf8'
            )

    except Exception as exc:
        # save a message in database
        submission.status = Submission.STATUSES.get_value('error')
        submission.message = str(exc)
        submission.save()

        # debug
        logger.error("error in calling upload_cryoweb: %s" % (exc))

        return False

    else:
        n_of_statements = len(result.stdout.split("\n"))
        logger.debug("%s statement executed" % n_of_statements)

        for line in result.stderr.split("\n"):
            logger.error(line)

        logger.info("{filename} uploaded into cryoweb {database}".format(
            filename=submission.uploaded_file.name, database=database_name))

    return True


# HINT: move to image_app.helpers?
# TODO: call this **BEFORE** loading data into cryoweb
def check_UID():
    """A function to ensure that UID is valid before data upload. Specific
    to the module where is called from"""

    pass


def import_from_cryoweb(submission_id):
    """Import data from cryoweb stage database into UID

    :submission_id: the submission primary key
    """

    pass
