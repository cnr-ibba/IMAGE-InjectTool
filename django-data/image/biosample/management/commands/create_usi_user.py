#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 20 10:06:37 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import sys
import json
import logging
import getpass

from decouple import AutoConfig
from django.conf import settings
from django.core.management import BaseCommand

from pyEBIrest.client import User
from pyEBIrest.auth import Auth

# Get an instance of a logger
logger = logging.getLogger(__name__)

# change the default level for pyEBIrest logging
logging.getLogger('pyEBIrest.auth').setLevel(logging.INFO)
logging.getLogger('pyEBIrest.client').setLevel(logging.INFO)

# define a decouple config object
settings_dir = os.path.join(settings.BASE_DIR, 'image')
config = AutoConfig(search_path=settings_dir)


class Command(BaseCommand):
    help = 'Create a USI user'

    def add_arguments(self, parser):
        parser.add_argument(
            '-u',
            '--username',
            type=str,
            required=True,
            help="The new USI username")

        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help="New user email")

        parser.add_argument(
            '--full_name',
            type=str,
            required=True,
            nargs='+',
            help="New user full name")

        parser.add_argument(
            '--organization',
            type=str,
            help="New user organization (default: '%(default)s')",
            default="IMAGE")

        parser.add_argument(
            '--description',
            type=str,
            help="New team description")

    def handle(self, *args, **options):
        # call commands and fill tables.
        logger.info("Called %s" % (sys.argv[1]))

        # create a new auth object
        auth = Auth(
            user=config('USI_MANAGER'),
            password=config('USI_MANAGER_PASSWORD'))

        # TODO: check if usernames exists

        # get password from stdin
        password = getpass.getpass(
            "User %s please type your password: " % (options['username']))
        confirmPwd = getpass.getpass("Please confirm password: ")

        # set full name as
        full_name = " ".join(options['full_name'])

        logger.debug("This are your data:")
        logger.debug(
            (
                options['username'],
                password,
                confirmPwd,
                options['email'],
                full_name,
                options['organization']
            )
        )

        # creating a user
        logger.debug("Creating user...")

        try:
            user_id = User.create_user(
                user=options['username'],
                password=password,
                confirmPwd=confirmPwd,
                email=options['email'],
                full_name=full_name,
                organization=options['organization']
            )

        except ConnectionError as e:
            logger.error("Problem in creating user %s" % (options['username']))
            logger.error("Message was: %s" % (json.loads(str(e))['message']))
            raise e

        # creating a new team. First create an user object
        admin = User(auth)

        if not options['description']:
            options['description'] = "Team for %s" % (options['username'])

        # now create a team
        logger.debug("Creating team...")
        team = admin.create_team(description=options['description'])
        logger.info("Team %s generated" % (team.name))

        # I need to generate a new token to see the new team
        logger.debug("Generate a new token")

        auth = Auth(
            user=config('USI_MANAGER'),
            password=config('USI_MANAGER_PASSWORD'))

        # pass the new auth object to admin
        admin.auth = auth

        # list all domain for manager
        logger.debug("Listing all domains for %s" % (config('USI_MANAGER')))
        logger.debug(", ".join(auth.claims['domains']))

        # get the domain for the new team, and then the domain_id
        logger.debug("Getting domain info for team %s" % (team.name))
        domain = admin.get_domain_by_name(team.name)
        domain_id = domain.domainReference

        logger.debug(
            "Adding user %s to team %s" % (options['username'], team.name))

        admin.add_user_to_team(user_id=user_id, domain_id=domain_id)

        # completed
        logger.info("%s ended" % (sys.argv[1]))
