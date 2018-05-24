from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import django
import pip
import os

PROJECT_REQUIREMENTS = settings.REQUIREMENTS #r'conf\requirements.txt'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)


class Command(BaseCommand):

    help = 'Install packages and migrate models.'

    def handle(self, **options):
        django.setup()
        pip.main(['install', '-r', PROJECT_REQUIREMENTS])
        call_command('bower', 'install')
        call_command('makemigrations')
        call_command('migrate')