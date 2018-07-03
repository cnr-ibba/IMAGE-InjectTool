
from django.test import TestCase

from ..forms import SignUpUserForm, SignUpPersonForm, SignUpForm


# test FormClass itself, not a view
class SignUpUserFormTest(TestCase):
    def test_form_has_fields(self):
        form = SignUpUserForm()
        expected = [
            'username', 'first_name', 'last_name', 'email', 'password1',
            'password2']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)


class SignUpPersonFormTest(TestCase):
    def test_form_has_fields(self):
        form = SignUpPersonForm()
        expected = [
            'initials', 'affiliation', 'role', 'organization', 'agree_gdpr',
            'botcatcher']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)


class SignUpFormTest(TestCase):
    def test_form_has_fields(self):
        form = SignUpForm()
        expected = [
            'username', 'first_name', 'last_name', 'email', 'password1',
            'password2', 'initials', 'affiliation', 'role', 'organization',
            'agree_gdpr', 'botcatcher']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)
