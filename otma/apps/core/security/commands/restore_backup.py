from otma.apps.core.security.services import GDriveClient
from django.core.management.base import BaseCommand
from django.conf import settings
import django
import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)


class Command(BaseCommand):
    help = 'Print hello world'

    def add_arguments(self, parser):
        parser.add_argument('specific_file', nargs='*')

    def handle(self, **options):

        django.setup()

        if options['specific_file']:
            number = options['specific_file'][0]
            restore = GDriveClient().restore_backup(int(number))
        else:
            restore = GDriveClient().restore_backup()

        print(restore)


"""
class Command(BaseCommand):
    help = 'Restore last backup.'

    def handle(self, **options):

        '''
            path = 'data/backup/temp.dump'
            path_zip = 'data/backup/temp.dump.gz'
            connector = SqliteCPConnector()
            dump = connector.create_dump()
            with open(path, 'wb') as f:
                f.write(dump.read())
            with open(path, 'rb') as f:
                data = f.read()
            with gzip.open(path_zip, 'wb') as f:
                f.write(data)
                f.close()
            #file_dump = BackupManager().download_last_file()
            #print(file_dump)
            with gzip.open(path_zip, 'rb') as f:
                file_content = BytesIO(f.read())
            connector.restore_dump(file_content)
        '''

        django.setup()
        #call_command('flush', '--no-input')
        restore = BackupManager().restore_backup()
        print(restore)"""
