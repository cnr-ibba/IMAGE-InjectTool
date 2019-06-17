from django.test import Client, TestCase
from django.urls import resolve, reverse

from common.tests import GeneralMixinTestCase, OwnerMixinTestCase

from ..views import SubmissionValidationSummaryView


class SubmissionValidationSummaryViewTest(GeneralMixinTestCase,
                                          OwnerMixinTestCase, TestCase):
    """Test Submission DetailView"""
    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission",
        "validation/validationsummary"
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url_animals = reverse('submissions:validation_summary', kwargs={
            'pk': 1, 'type': 'animals'})
        self.url_samples = reverse('submissions:validation_summary', kwargs={
            'pk': 1, 'type': 'samples'})
        self.url = self.url_animals
        self.response = self.client.get(self.url_animals)

    def test_url_resolves_view_for_animals(self):
        view = resolve('/submissions/1/validation_summary/animals/')
        self.assertIsInstance(view.func.view_class(),
                              SubmissionValidationSummaryView)

    def test_url_resolves_view_for_samples(self):
        view = resolve('/submissions/1/validation_summary/samples/')
        self.assertIsInstance(view.func.view_class(),
                              SubmissionValidationSummaryView)

    def test_new_not_found_status_code_for_animals(self):
        url = reverse('submissions:validation_summary', kwargs={
            'pk': 99, 'type': 'animals'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_new_not_found_status_code_for_samples(self):
        url = reverse('submissions:validation_summary', kwargs={
            'pk': 99, 'type': 'samples'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_ownership_for_animals(self):
        """Test ownership for a submissions"""

        client = Client()
        client.login(username='test2', password='test2')

        response = client.get(self.url_animals)
        self.assertEqual(response.status_code, 404)

    def test_ownership_for_samples(self):
        """Test ownership for a submissions"""

        client = Client()
        client.login(username='test2', password='test2')

        response = client.get(self.url_samples)
        self.assertEqual(response.status_code, 404)

    def test_contains_mesages_for_animals(self):
        """test validation summary badges and messages"""
        response = self.client.get(self.url_animals)
        self.assertContains(response, "Pass: 0")
        self.assertContains(response, "Warnings: 1")
        self.assertContains(response, "Errors: 0")
        self.assertContains(response, "JSON Errors: 0")
        self.assertContains(response, "Wrong JSON structure")

    def test_contains_mesages_for_samples(self):
        """test validation summary badges and messages"""
        response = self.client.get(self.url_samples)
        self.assertContains(response, "Pass: 0")
        self.assertContains(response, "Warnings: 0")
        self.assertContains(response, "Errors: 0")
        self.assertContains(response, "JSON Errors: 0")
        self.assertContains(response, "Wrong JSON structure")
