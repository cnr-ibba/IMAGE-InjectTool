import os
import unittest

import pandas as pd
from django.conf import settings
from django.core.management import BaseCommand

from image_app import helpers
from image_app.models import Animal, DataSource


class Command(BaseCommand):
    # This will be displayed when calling: python manage.py mycheck --help
    help = """Performs a series of checks on the real Image database"""

    def handle(self, *args, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDB)
        unittest.TextTestRunner().run(suite)


class TestDB(unittest.TestCase):
    """Testing database status"""

    def setUp(self):
        # get a cryoweb helper instance
        self.cryowebdb = helpers.CryowebDB()

        # get a connection object
        self.conn = self.cryowebdb.get_connection(search_path='apiis_admin')

    def test_db1_animal_table_is_not_empty(self):
        """Tests that cryoweb.animal table is not empty"""

        df_count = pd.read_sql_query(
                'select count(*) as n_rows from animal',
                con=self.conn)

        # pprint.pprint(df_count['n_rows'].values[0])
        self.assertTrue(int(df_count['n_rows'].values[0]) > 0)

    def test_db2_animal_table_is_not_empty(self):
        """Tests that image animal table is not empty"""

        # pprint.pprint(df_count['n_rows'].values[0])
        self.assertTrue(Animal.objects.count() > 0,
                        msg="%s.%s table is empty!!!" % (
                                settings.DATABASES['default']['NAME'],
                                Animal._meta.db_table))

    def test_no_orphaned_backup_files_in_filesys(self):
        """Tests no orphaned backup files in /media/data_source dir"""

        # get the file list from the filesystem
        data_source_dir = os.path.join(
                settings.MEDIA_ROOT,
                DataSource.upload_dir)

        data_source_files = os.listdir(data_source_dir)

        # prepend DataSource.upload_dir to file list
        data_source_files = [
                os.path.join(
                        DataSource.upload_dir,
                        uploaded_file)
                for uploaded_file in data_source_files]

        # get the file list from the db
        queryset = DataSource.objects.all()
        database_files = [
                str(datasource.uploaded_file) for datasource in queryset]

        # HINT: are two list in the same order?
        self.assertListEqual(data_source_files,
                             database_files,
                             "\n "
                             "\n Orphaned backup files found "
                             "\n in {}"
                             "\n try "
                             "\n $ ...manage.py clean_backup command "
                             "".format(settings.MEDIA_ROOT))
