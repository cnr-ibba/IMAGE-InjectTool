import os

from django.conf import settings
from django.core.management import BaseCommand, call_command

from image_app.models import Submission


class Command(BaseCommand):
    help = """
    Deletes orphaned backup files: files in filesystem without any
    correspondence in the backup table are deleted. Their existance is due to
    a behaviour of django: files are deleted from the database but not
    fisically from the filesystem. This command calls also mycheck after its
    function.
    """

    def handle(self, *args, **options):
        # get the file list from the filesystem
        data_source_dir = os.path.join(
                settings.MEDIA_ROOT,
                Submission.upload_dir)

        data_source_files = os.listdir(data_source_dir)

        # prepend DataSource.upload_dir to file list
        data_source_files = [
                os.path.join(
                        Submission.upload_dir,
                        uploaded_file)
                for uploaded_file in data_source_files]

        # get the file list from the db
        queryset = Submission.objects.all()
        database_files = [
                str(datasource.uploaded_file) for datasource in queryset]

        for datasource_file in data_source_files:
            if datasource_file not in database_files:
                to_remove = os.path.join(
                        settings.MEDIA_ROOT,
                        datasource_file)

                # debug
                print("Removing %s" % (to_remove))
                os.remove(to_remove)

        call_command('mycheck')
