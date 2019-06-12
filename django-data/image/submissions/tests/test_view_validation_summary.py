from django.test import Client, TestCase
from django.urls import resolve, reverse

from common.tests import GeneralMixinTestCase, OwnerMixinTestCase

from ..views import SubmissionValidationSummaryView


class SubmissionValidationSummaryViewTest(TestCase):
    """Test Submission DetailView"""
    fixtures = [
        "image_app/user",
        "image_app/dictcountry",
        "image_app/dictrole",
        "image_app/organization",
        "image_app/submission"
    ]

    def setUp(self):
        # login a test user (defined in fixture)
        self.client = Client()
        self.client.login(username='test', password='test')

        self.url_animals = reverse('submissions:validation_summary', kwargs={
            'pk': 1, 'type': 'animals'})
        self.url_samples = reverse('submissions:validation_summary', kwargs={
            'pk': 1, 'type': 'samples'})

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
