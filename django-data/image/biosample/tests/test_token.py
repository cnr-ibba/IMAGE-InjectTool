#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 17 10:59:01 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import python_jwt
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from ..models import Account, ManagedTeam
from ..views import TokenView
from .session_enabled_test_case import SessionEnabledTestCase


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


class TestTokenView(SessionEnabledTestCase):
    fixtures = [
        "biosample/managedteam.json"
    ]

    def setUp(self):
        User = get_user_model()

        # create a testuser
        user = User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        team = ManagedTeam.objects.get(name="subs.test-team-1")
        Account.objects.create(
            user=user, team=team, name="image-test")

        self.client = Client()
        self.client.login(username='test', password='test')

        # get the url for dashboard
        self.url = reverse('biosample:token')
        self.response = self.client.get(self.url)

    def check_messages(self, response, tag, message_text):
        """Check that a response has warnings"""

        # each element is an instance
        # of django.contrib.messages.storage.base.Message
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        found = False

        # I can have moltiple message, and maybe I need to find a specific one
        for message in all_messages:
            if tag in message.tags and message_text in message.message:
                found = True

        self.assertTrue(found)

    def test_redirection(self):
        '''Non Authenticated user are directed to login page'''

        login_url = reverse("login")
        client = Client()
        response = client.get(self.url)

        self.assertRedirects(
            response, '{login_url}?next={url}'.format(
                login_url=login_url, url=self.url)
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_url_resolves_view(self):
        view = resolve('/biosample/token/')
        self.assertIsInstance(view.func.view_class(), TokenView)

    def test_contains_navigation_links(self):
        dashboard_url = reverse('image_app:dashboard')
        newtoken_url = reverse('biosample:token-generation')

        self.assertContains(self.response, 'href="{0}"'.format(dashboard_url))
        self.assertContains(self.response, 'href="{0}"'.format(newtoken_url))

    def test_biosample_account(self):
        self.assertContains(self.response, 'image-test')
        self.assertContains(self.response, 'subs.test-team-1')

    def test_no_token_generated(self):
        self.check_messages(
            self.response,
            "error",
            "You haven't generated any token yet")

    def test_valid_tocken(self):
        session = self.get_session()
        session['token'] = generate_token()
        session.save()
        self.set_session_cookies(session)

        response = self.client.get(self.url)
        self.assertContains(response, 'Token for Foo Bar will last')

    def test_expired_token(self):
        session = self.get_session()
        now = int(timezone.now().timestamp())
        session['token'] = generate_token(now-10000)
        session.save()
        self.set_session_cookies(session)

        response = self.client.get(self.url)

        self.assertContains(response, 'Token for Foo Bar is expired')

        self.check_messages(
            response,
            "error",
            "Your token is expired")


class NewTokenViewTest(TestCase):
    def setUp(self):
        User = get_user_model()

        # create a testuser
        User.objects.create_user(
            username='test',
            password='test',
            email="test@test.com")

        self.client = Client()
        self.client.login(username='test', password='test')

        # get the url for dashboard
        self.url = reverse('biosample:token')
        self.response = self.client.get(self.url)

    def test_redirection(self):
        '''Non Authenticated user are directed to login page'''

        login_url = reverse("login")
        client = Client()
        response = client.get(self.url)

        self.assertRedirects(
            response, '{login_url}?next={url}'.format(
                login_url=login_url, url=self.url)
        )

    def test_registered(self):
        """A non registered user is redirected to "activate complete"""

        target_url = reverse('accounts:registration_activation_complete')

        self.assertRedirects(self.response, target_url)
