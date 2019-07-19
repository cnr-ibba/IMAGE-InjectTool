#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 15:15:09 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import redis
import python_jwt

from billiard.einfo import ExceptionInfo
from unittest.mock import patch, PropertyMock

from django.core import mail
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from common.constants import READY, ERROR
from common.tests import PersonMixinTestCase, WebSocketMixin
from image_app.models import Submission, Person, Name


def generate_token(now=None, domains=['subs.test-team-1']):
    """A function to generate a 'fake' token"""

    if not now:
        now = int(timezone.now().timestamp())

    claims = {
        'iss': 'https://explore.aai.ebi.ac.uk/sp',
        'iat': now,
        'exp': now+3600,
        'sub': 'usr-f1801430-51e1-4718-8fca-778887087bad',
        'email': 'foo.bar@email.com',
        'nickname': 'foo',
        'name': 'Foo Bar',
        'domains': domains
    }

    return python_jwt.generate_jwt(
        claims,
        algorithm='RS256')


class BaseMixin(PersonMixinTestCase):
    # an attribute for PersonMixinTestCase
    person = Person

    fixtures = [
        'biosample/account',
        'biosample/managedteam',
        'image_app/animal',
        'image_app/dictbreed',
        'image_app/dictcountry',
        'image_app/dictrole',
        'image_app/dictsex',
        'image_app/dictspecie',
        'image_app/dictstage',
        'image_app/dictuberon',
        'image_app/name',
        'image_app/ontology',
        'image_app/organization',
        'image_app/publication',
        'image_app/sample',
        'image_app/submission',
        'image_app/user'
    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # get a submission object
        self.submission_obj = Submission.objects.get(pk=1)

        # set a status which I can submit
        self.submission_obj.status = READY
        self.submission_obj.save()

        # get the names I want to submit
        self.name_qs = Name.objects.filter(
            Q(animal__isnull=False) | Q(sample__isnull=False),
            submission=self.submission_obj)

        # set status for names, like validation does. Update only animal
        # and sample names (excluding unkwnon animals)
        self.name_qs.update(status=READY)

        # count number of names in UID for such submission (exclude
        # unknown animals)
        self.n_to_submit = self.name_qs.count()

        # track submission ID
        self.submission_id = self.submission_obj.id

        # starting mocked objects
        self.mock_root_patcher = patch('pyUSIrest.client.Root')
        self.mock_root = self.mock_root_patcher.start()

        # start root object
        self.my_root = self.mock_root.return_value

        # mocking chain
        self.my_team = self.my_root.get_team_by_name.return_value
        self.my_team.name = "subs.test-team-1"

        # mocking a new submission
        self.new_submission = self.my_team.create_submission.return_value
        self.new_submission.name = "new-submission"

        # set status. Because of the way mock attributes are stored you can’t
        # directly attach a PropertyMock to a mock object. Instead you can
        # attach it to the mock type object:
        self.new_submission.propertymock = PropertyMock(return_value='Draft')
        type(self.new_submission).status = self.new_submission.propertymock

        # mocking get_submission_by_name
        self.my_submission = self.my_root.get_submission_by_name.return_value
        self.my_submission.name = "test-submission"

        self.my_submission.propertymock = PropertyMock(return_value='Draft')
        type(self.my_submission).status = self.my_submission.propertymock


class TaskFailureMixin(WebSocketMixin, BaseMixin):
    def test_on_failure(self):
        """Testing on failure methods"""

        exc = Exception("Test")
        task_id = "test_task_id"
        args = [self.submission_id]
        kwargs = {}
        einfo = ExceptionInfo

        # call on_failure method
        self.my_task.on_failure(exc, task_id, args, kwargs, einfo)

        # check submission status and message
        submission = Submission.objects.get(pk=self.submission_id)

        # check submission.state changed
        self.assertEqual(submission.status, ERROR)
        self.assertEqual(
            submission.message,
            "Error in biosample submission: Test")

        # test email sent
        self.assertEqual(len(mail.outbox), 1)

        # read email
        email = mail.outbox[0]

        self.assertEqual(
            "Error in biosample submission %s" % self.submission_id,
            email.subject)

        message = 'Error'
        notification_message = 'Error in biosample submission: Test'

        # calling a WebSocketMixin method
        self.check_message(message, notification_message)


class RedisMixin():
    """A class to setup a test token in redis database"""

    # this will be the token key in redis database
    submission_key = "token:submission:1:test"

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        cls.redis = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB)

        # generate a token
        cls.token = generate_token(domains=['subs.test-team-1'])

        # write token to database
        cls.redis.set(cls.submission_key, cls.token, ex=3600)

    @classmethod
    def tearDownClass(cls):
        if cls.redis.exists(cls.submission_key):
            cls.redis.delete(cls.submission_key)

        super().tearDownClass()
