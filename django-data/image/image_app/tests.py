from django.test import TestCase
import pandas as pd

from image_app.models import Submission, Person, Organization, Publication, \
    Database, Term_source

class HeaderBuildTest(TestCase):

    def test_read_organisations(self):
        """Organizations are correctely read from the database"""

        print('test organization...')
        orgs = Organization.objects.all()
        for o in orgs:
            self.assertEqual(str(o), "asd")
            self.assertEqual("asds", "asd")
