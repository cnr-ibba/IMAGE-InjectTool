from django.core.management import BaseCommand
import os
import glob
import unittest
import pandas as pd
from sqlalchemy import create_engine
# import pprint
import subprocess
from django.conf import settings
from django.core.management import call_command

class Command(BaseCommand):
    help = """
    	Deletes orphaned backup files: files in filesystem without any correspondence in the backup table are deleted.
    	Their existance is due to a behaviour of django: files are deleted from the database but not fisically
    	from the filesystem. This command calls also mycheck after its function.
    """

    def handle(self, *args, **options):

        engine_to_sampletab = create_engine('postgresql://postgres:***REMOVED***@db:5432/image')

        # get the file list from the filesystem
        os.chdir(settings.MEDIA_ROOT)
        ls_from_filesys = glob.glob("backups/*.sql")
        print("ls_from_filesys:\n{}".format(ls_from_filesys))

        # get the file list from the db
        ls_from_db = pd.read_sql_query('select backup from image_app_backup', con=engine_to_sampletab)
        ls_from_db = list(ls_from_db['backup'])
        print("ls_from_db:\n{}".format(ls_from_db))

        for elem in ls_from_filesys:
            if elem not in ls_from_db:
                os.remove(elem)

        call_command('mycheck')
