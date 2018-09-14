"""
Downloaded: https://gist.github.com/dustinfarris/4982145

Attempting to set session variables directly from TestCases can
be error prone.  Use this super-class to enable session modifications
from within your tests.

Usage
-----

class MyTest(SessionEnabledTestCase):

    def test_with_session_support(self):
        session = self.get_session()
        session['some-key'] = 'some-value'
        session.save()
        self.set_session_cookies(session)

        response = self.client.get('/')

        self.assertIn(
            ('some-key', 'some-value'),
            response.client.session.items())

"""

from importlib import import_module

from django.conf import settings as django_settings
from django.test import TestCase


class SessionEnabledTestCase(TestCase):

    def get_session(self):
        if self.client.session:
            session = self.client.session
        else:
            engine = import_module(django_settings.SESSION_ENGINE)
            session = engine.SessionStore()
        return session

    def set_session_cookies(self, session):
        # Set the cookie to represent the session
        session_cookie = django_settings.SESSION_COOKIE_NAME
        self.client.cookies[session_cookie] = session.session_key
        cookie_data = {
            'max-age': None,
            'path': '/',
            'domain': django_settings.SESSION_COOKIE_DOMAIN,
            'secure': django_settings.SESSION_COOKIE_SECURE or None,
            'expires': None}
        self.client.cookies[session_cookie].update(cookie_data)
