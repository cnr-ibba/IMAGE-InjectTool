
from django.test import TestCase

from ..forms import (
    SignUpUserForm, SignUpPersonForm, SignUpForm, UserForm, PersonForm)


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
            'initials', 'affiliation', 'role', 'organization', 'agree_gdpr']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)


class SignUpFormTest(TestCase):
    def test_form_has_fields(self):
        form = SignUpForm()
        expected = [
            'username', 'first_name', 'last_name', 'email', 'password1',
            'password2', 'initials', 'affiliation', 'role', 'organization',
            'agree_gdpr']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)


class UserFormTest(TestCase):
    def test_form_has_fields(self):
        form = UserForm()
        expected = ['first_name', 'last_name', 'email']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)


class PersonFormTest(TestCase):
    def test_form_has_fields(self):
        form = PersonForm()
        expected = ['initials', 'affiliation', 'role', 'organization']
        actual = list(field.name for field in form)
        self.assertSequenceEqual(expected, actual)