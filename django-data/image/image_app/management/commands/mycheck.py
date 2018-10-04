import os
import unittest

from django.conf import settings
from django.core.management import BaseCommand

from cryoweb.models import db_has_data as cryoweb_has_data
from image_app.models import Submission, db_has_data as image_has_data


class Command(BaseCommand):
    # This will be displayed when calling: python manage.py mycheck --help
    help = """Performs a series of checks on the real Image database"""

    def handle(self, *args, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDB)
        unittest.TextTestRunner().run(suite)


class TestDB(unittest.TestCase):
    """Testing database status"""

    def test_db1_animal_table_is_not_empty(self):
        """Tests that cryoweb.animal table is not empty"""

        self.assertFalse(
            cryoweb_has_data(),
            msg="%s database has data!!!" % (
                settings.DATABASES['cryoweb']['NAME']))

    def test_db2_animal_table_is_not_empty(self):
        """Tests that image animal table is not empty"""

        self.assertTrue(
            image_has_data(),
            msg="%s database is empty!!!" % (
                settings.DATABASES['default']['NAME']))

    def test_no_orphaned_backup_files_in_filesys(self):
        """Tests no orphaned backup files in /media/data_source dir"""

        # get the file list from the filesystem
        data_source_dir = os.path.join(
                settings.MEDIA_ROOT,
                Submission.upload_dir)

        data_source_files = os.listdir(data_source_dir)

        # prepend Submission.upload_dir to file list
        data_source_files = [
                os.path.join(
                        Submission.upload_dir,
                        uploaded_file)
                for uploaded_file in data_source_files]

        # get the file list from the db
        queryset = Submission.objects.all()
        database_files = [
                str(datasource.uploaded_file) for datasource in queryset]

        # Order the two lists
        data_source_files.sort()
        database_files.sort()

        self.assertListEqual(
            data_source_files,
            database_files,
            "\n "
            "\n Orphaned backup files found "
            "\n in {}"
            "\n try "
            "\n $ ...manage.py clean_backup command "
            "".format(settings.MEDIA_ROOT))
