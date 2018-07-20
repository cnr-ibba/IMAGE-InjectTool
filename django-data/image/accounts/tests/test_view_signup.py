
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse

from ..forms import SignUpForm
from ..views import SignUpView


# Create your tests here.
class SignUpTests(TestCase):
    def setUp(self):
        url = reverse('accounts:registration_register')
        self.response = self.client.get(url)

    def test_signup_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_signup_url_resolves_signup_view(self):
        view = resolve('/accounts/register/')
        self.assertIsInstance(view.func.view_class(), SignUpView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')

        self.assertIsInstance(form, SignUpForm)

    def test_form_inputs(self):
        '''
        The view must contain eleven inputs: csrf, username, first_name,
        last_name, email, password1, password2, affiliation, role,
        organization and agree_gdpr checkbox
        '''

        self.assertContains(self.response, '<input', 11)
        self.assertContains(self.response, 'type="text"', 5)
        self.assertContains(self.response, 'type="email"', 1)
        self.assertContains(self.response, 'type="password"', 2)


class SuccessfulSignUpTests(TestCase):
    fixtures = [
        "dictcountry.json", "dictrole.json", "organization.json"
    ]

    def setUp(self):
        self.url = reverse('accounts:registration_register')

        # SignUpForm is a multiform object, so input type name has the name of
        # the base form and the name of the input type
        self.data = {
            'user-username': 'john',
            'user-first_name': 'John',
            'user-last_name': 'Doe',
            'user-email': 'john@doe.com',
            'user-password1': 'abcdef123456',
            'user-password2': 'abcdef123456',
            'person-affiliation': 'IBBA',
            'person-role': 1,
            'person-organization': 1,
            'person-agree_gdpr': True
        }
        self.response = self.client.post(self.url, self.data)
        self.complete_url = reverse('accounts:registration_complete')
        self.home_url = reverse('index')

    def test_redirection(self):
        '''
        A valid form submission should redirect the user registration complete
        '''

        self.assertRedirects(self.response, self.complete_url)

    def test_resend_page(self):
        """Follow the redirects and ensure that a resend link is present"""

        # follow url
        response = self.client.get(self.response.url)

        # set the url for re-send activation
        target_url = reverse("accounts:registration_resend_activation")
        self.assertContains(response, 'href="{0}"'.format(target_url))

    def test_user_creation(self):
        self.assertTrue(User.objects.exists())

    def test_user_authentication(self):
        '''
        Create a new request to an arbitrary page.
        The resulting response should now have a `user` to its context,
        but since there was no activation, the user can't login.
        '''
        response = self.client.get(self.home_url)
        user = response.context.get('user')
        self.assertFalse(user.is_authenticated)


class InvalidSignUpTests(TestCase):
    def check_messages(self, response, tag, message_text):
        """Check that a response has warnings"""

        # each element is an instance
        # of django.contrib.messages.storage.base.Message
        all_messages = [msg for msg in get_messages(response.wsgi_request)]

        for message in all_messages:
            self.assertTrue(tag in message.tags)
            self.assertEqual(
                message.message,
                message_text)

    def setUp(self):
        url = reverse('accounts:registration_register')
        self.response = self.client.post(url, {})  # submit an empty dictionary

    def test_signup_status_code(self):
        '''
        An invalid form submission should return to the same page
        '''
        self.assertEquals(self.response.status_code, 200)

    def test_form_errors(self):
        multi_form = self.response.context.get('form')
        for form in multi_form.forms.values():
            self.assertGreater(len(form.errors), 0)

    def test_form_messages(self):
        self.check_messages(
            self.response,
            "error",
            "Please correct the errors below")

    def test_dont_create_user(self):
        self.assertFalse(User.objects.exists())
