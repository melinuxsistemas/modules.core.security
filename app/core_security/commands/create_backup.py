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
        backup.save()
