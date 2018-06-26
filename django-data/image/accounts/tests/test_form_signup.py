
from django.test import TestCase

from ..forms import SignUpForm, UserForm, PersonForm


# test FormClass itself, not a view
class SignUpFormTest(TestCase):
    def test_form_has_fields(self):
        form = SignUpForm()
        expected = [
            'username', 'first_name', 'last_name', 'email', 'password1',
            'password2']
        actual = list(form.fields)
        self.assertSequenceEqual(expected, actual)


class UserFormTest(TestCase):
    def test_form_has_fields(self):
        form = UserForm()
        expected = ['first_name', 'last_name', 'email']
        actual = list(form.fields)
        self.assertSequenceEqual(expected, actual)


class PersonFormTest(TestCase):
    def test_form_has_fields(self):
        form = PersonForm()
        expected = ['initials', 'affiliation', 'role', 'organization']
        actual = list(form.fields)
        self.assertSequenceEqual(expected, actual)
