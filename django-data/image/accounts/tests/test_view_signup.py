
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import resolve, reverse

from ..views import SignUpView


# Registration is closed (SignUpView.registration_allowed returns False)
class SignUpTests(TestCase):
    def setUp(self):
        self.url = reverse('accounts:registration_register')
        self.closed_url = reverse('accounts:registration_disallowed')

    def test_signup_url_resolves_signup_view(self):
        view = resolve('/accounts/register/')
        self.assertIsInstance(view.func.view_class(), SignUpView)

    def test_signup_redirects_to_closed(self):
        """GET on signup page redirects to the registration closed page"""

        response = self.client.get(self.url)
        self.assertRedirects(response, self.closed_url)

    def test_closed_page(self):
        response = self.client.get(self.closed_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registration is currently closed")

    def test_post_doesnt_create_user(self):
        """A valid signup submission is redirected and doesn't register"""

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

        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.closed_url)
        self.assertFalse(User.objects.exists())
        self.assertEqual(len(mail.outbox), 0)
