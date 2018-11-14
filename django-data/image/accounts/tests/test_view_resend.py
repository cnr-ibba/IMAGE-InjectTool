#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 17:12:06 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

Test resend keys stuff

"""

from django.core import mail
from django.test import TestCase
from django.urls import resolve, reverse
from django.contrib.auth.models import User

from registration.forms import ResendActivationForm

from ..views import ResendActivationView
from ..models import MyRegistrationProfile


# Create your tests here.
class ResendActivationViewTest(TestCase):
    def setUp(self):
        url = reverse('accounts:registration_resend_activation')
        self.response = self.client.get(url)

    def test_signup_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_signup_url_resolves_signup_view(self):
        view = resolve('/accounts/activate/resend/')
        self.assertIsInstance(view.func.view_class(), ResendActivationView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')

        self.assertIsInstance(form, ResendActivationForm)

    def test_form_inputs(self):
        '''
        The view must contain eleven inputs: csrf, username, first_name,
        last_name, email, password1, password2, affiliation, role,
        organization and agree_gdpr checkbox
        '''

        self.assertContains(self.response, '<input', 2)
        self.assertContains(self.response, 'type="email"', 1)


class BaseTest(TestCase):
    fixtures = [
        "image_app/dictcountry.json",
        "image_app/dictrole.json",
        "accounts/organization.json"
    ]

    def setUp(self):
        url = reverse('accounts:registration_register')

        # SignUpForm is a multiform object, so input type name has the name of
        # the base form and the name of the input type
        data = {
            'user-username': 'john',
            'user-first_name': 'John',
            'user-last_name': 'Doe',
            'user-email': 'john@doe.com',
            'user-password1': 'abcdef123456',
            'user-password2': 'abcdef123456',
            'person-affiliation': 1,
            'person-role': 1,
            'person-agree_gdpr': True
        }

        self.client.post(url, data, follow=True)

        # get the resend url
        self.url = reverse("accounts:registration_resend_activation")


class SuccessResendActivationViewTest(BaseTest):
    def test_send_email(self):
        data = {'email': 'john@doe.com'}
        response = self.client.post(self.url, data)

        self.assertContains(response, "A confirmation email has been sent "
                                      "to the email used for registration.")


class InvalidResendActivationViewTest(BaseTest):
    def test_send_invalid_mail(self):
        data = {'email': 'foo@bar.com'}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)

        form = response.context.get('form')
        self.assertGreater(len(form.errors), 0)

    def test_sent_active_mail(self):
        """test already active email"""

        # consider email for activation
        n_of_messages = len(mail.outbox)

        # get a profile object
        profile = MyRegistrationProfile.objects.get(
                user__email__iexact='john@doe.com')

        # set profile as activated
        profile.activated = True
        profile.save()

        user = User.objects.get(username='john')
        user.is_active = True
        user.save()

        data = {'email': 'john@doe.com'}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)

        form = response.context.get('form')
        self.assertGreater(len(form.errors), 0)

        # no mail are sent
        self.assertEqual(len(mail.outbox), n_of_messages)

    # This will be avoided during registration
    def test_double_email(self):
        """test email used two times"""

        # create a user with the same email as the registered one
        user = User.objects.create_user(
            username='test',
            password='test',
            email="john@doe.com")

        # I need to add a registrationProfile record
        profile = MyRegistrationProfile(user=user)
        profile.save()

        # consider email for activation
        n_of_messages = len(mail.outbox)

        data = {'email': 'john@doe.com'}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)

        form = response.context.get('form')
        self.assertGreater(len(form.errors), 0)

        # no mail are sent
        self.assertEqual(len(mail.outbox), n_of_messages)
