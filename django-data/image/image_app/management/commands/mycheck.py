from django.core.management import BaseCommand
import os
import glob
import unittest
import pandas as pd
from sqlalchemy import create_engine
# import pprint
import subprocess
from django.conf import settings

class Command(BaseCommand):
    help = """
    	Performs a series of checks on the real Image database.
    """

    def handle(self, *args, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDB)
        unittest.TextTestRunner().run(suite)
        # self.stdout.write("qui stampo quello che voglio", ending='')


class TestDB(unittest.TestCase):
    engine_from_cryoweb = None
    engine_to_sampletab = None

    def setUp(self):
        self.engine_from_cryoweb = create_engine('postgresql://postgres:***REMOVED***@db:5432/imported_from_cryoweb')
        self.engine_to_sampletab = create_engine('postgresql://postgres:***REMOVED***@db:5432/image')

    # def test_equality(self):
    #     """Tests that 1 + 1 always equals 2"""
    #     print("\ntest: 1 + 1 = 2 ...")
    #
    #     self.assertEqual(1 + 1, 1)

    def test_db1_animal_table_is_not_empty(self):
        """Tests that db1 (imported_from_cryoweb db) animal table is not empty"""
        print("\ntest: db1.animal not empty ...")

        df_count = pd.read_sql_query('select count(*) as n_rows from animal', con=self.engine_from_cryoweb)
        # pprint.pprint(df_count['n_rows'].values[0])
        self.assertTrue(int(df_count['n_rows'].values[0]) > 0)

    def test_db2_animals_table_is_not_empty(self):
        """Tests that db2 (image database) animals table is not empty"""
        print("\ntest: db2.animals not empty ...")

        df_count = pd.read_sql_query('select count(*) as n_rows from animals', con=self.engine_to_sampletab)
        # pprint.pprint(df_count['n_rows'].values[0])
        self.assertTrue(int(df_count['n_rows'].values[0]) > 0)

    def test_no_orphaned_backup_files_in_filesys(self):
        """Tests that db2 (image database) animals table is not empty"""
        print("\ntest: no orphaned backup files in /media/backup dir ...")

        # get the file list from the filesystem
        os.chdir(settings.MEDIA_ROOT)
        ls_from_filesys = glob.glob("backups/*.sql")
        # print(ls_from_filesys)

        # get the file list from the db
        ls_from_db = pd.read_sql_query('select backup from image_app_backup', con=self.engine_to_sampletab)
        ls_from_db = list(ls_from_db['backup'])
        # print(ls_from_db)

        self.assertListEqual(ls_from_db, ls_from_filesys, "\n "
                                                          "\n Orphaned backup files found "
                                                          "\n in {}"
                                                          "\n try "
                                                          "\n $ ...manage.py clean_backup command "
                                                          "".format(settings.MEDIA_ROOT))


