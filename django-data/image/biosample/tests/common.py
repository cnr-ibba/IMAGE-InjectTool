#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 15:15:09 2019

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import json
import redis
import python_jwt

from billiard.einfo import ExceptionInfo
from unittest.mock import patch, PropertyMock, Mock

from django.core import mail
from django.conf import settings
from django.utils import timezone

from common.constants import READY, ERROR, WAITING
from common.tests import WebSocketMixin
from uid.models import Submission, Animal, Sample
from uid.tests import PersonMixinTestCase

# the token will last for 24h (in seconds)
TOKEN_DURATION = 24*60*60

# get my path
dir_path = os.path.dirname(os.path.realpath(__file__))

# define data path
DATA_PATH = os.path.join(dir_path, "data")


def generate_token(now=None, exp=None, domains=['subs.test-team-1']):
    """A function to generate a 'fake' token"""

    if not now:
        now = int(timezone.now().timestamp())

    if not exp:
        exp = now + TOKEN_DURATION

    claims = {
        'iss': 'https://explore.aai.ebi.ac.uk/sp',
        'iat': now,
        'exp': exp,
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

    fixtures = [
        'biosample/account',
        'biosample/managedteam',
        'biosample/sample',
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
        'uid/submission',
        'uid/user'
    ]

    def setUp(self):
        # calling my base class setup
        super().setUp()

        # track submission ID
        self.submission_id = 1

        # get a submission object
        self.submission_obj = Submission.objects.get(pk=self.submission_id)

        # set a status which I can submit (equal as calling submit by view)
        self.submission_obj.status = WAITING
        self.submission_obj.message = "Waiting for biosample submission"
        self.submission_obj.save()

        # set status for objects, like submittask does.
        self.animal_qs = Animal.objects.all()
        self.animal_qs.update(status=READY)

        self.sample_qs = Sample.objects.all()
        self.sample_qs.update(status=READY)

        # count number of names in UID for such submission (exclude
        # unknown animals)
        self.n_to_submit = self.animal_qs.count() + self.sample_qs.count()

        # starting mocked objects
        self.mock_root_patcher = patch('pyUSIrest.usi.Root')
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
        kwargs = {'uid_submission_id': self.submission_id}
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
        self.assertEqual(len(mail.outbox), 2)

        # read email
        email = mail.outbox[-1]

        self.assertEqual(
            "Error in biosample submission for submission %s" % (
                self.submission_id),
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


class BioSamplesMixin():
    """Simulate fetching data from BioSamples"""

    @classmethod
    def setUpClass(cls):
        # calling my base class setup
        super().setUpClass()

        cls.mock_get_patcher = patch('requests.Session.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_get_patcher.stop()

        # calling base method
        super().tearDownClass()

    def setUp(self):
        # calling my base setup
        super().setUp()

        # simulate getting two data from biosamples
        with open(os.path.join(DATA_PATH, "SAMEA6376982.json")) as handle:
            sample1 = json.load(handle)

        with open(os.path.join(DATA_PATH, "SAMEA6376980.json")) as handle:
            sample2 = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.side_effect = [sample1, sample2]
        self.mock_get.return_value.status_code = 200
