from otma.apps.core.security.services import GDriveClient
from django.core.management.base import BaseCommand
from otma.apps.core.security.models import Backup
import datetime


class Command(BaseCommand):
    help = 'Print hello world'

    def add_arguments(self, parser):

        parser.add_argument(
            '--compressed',
            action='store_true',
            help='Comprimir e encriptar arquivos...',
        )

    def handle(self, **options):
        start_timing_backup = datetime.datetime.now()

        folder_id = GDriveClient().verify_folder()

        if options['compressed']:
            data = GDriveClient().create_backup(folder_id, compressed=True)
        else:
            data = GDriveClient().create_backup(folder_id)

        backup_duration = datetime.datetime.now() - start_timing_backup
        print("Backup gerado em", backup_duration.total_seconds(), "segundos")

        try:
            backup = Backup.objects.get(backup_file_name=data['file_name'])
        except:
            backup = Backup()

        backup.backup_file_name = data['file_name']
        backup.backup_link = data['link']
        backup.backup_size = data['size']
        backup.save()

"""
from app.core_security.services import BackupManager
from django.core.management.base import BaseCommand
from app.core_security.models import Backup


class Command(BaseCommand):
    help = 'Create remote backup'

    def handle(self, **options):
        backup_paramters = BackupManager().create_backup()
        try:
            backup = Backup.objects.get(backup_file_name=backup_paramters['file_name'])
        except:
            backup = Backup()

        backup.file_name = backup_paramters['file_name']
        backup.file_link = backup_paramters['link']
        backup.file_size = backup_paramters['size']
        backup.save()"""
