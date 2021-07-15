from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Tears down the database and calls the populate function'
    def handle(self, *args, **options):
        call_command('reset')
        call_command('makemigrations')
        call_command('migrate')
        call_command('populate')