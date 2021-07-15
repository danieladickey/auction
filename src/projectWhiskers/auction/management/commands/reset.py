from django.core.management.base import BaseCommand, CommandError
from auction.models import *
from django.contrib.auth.models import User
from pathlib import Path
import os


class Command(BaseCommand):
    help = 'reset database and migrations'

    def handle(self, *args, **options):
        try:
            os.remove('db.sqlite3')
            for file in os.listdir('auction/migrations/'):
                if file.startswith('000'):
                    os.remove('auction/migrations/'+file)
        except FileNotFoundError:
            print(FileNotFoundError)
            print("File already Removed")

        try:
            for file in os.listdir('media/auction'):
                os.remove('media/auction/'+file)
        except Exception:
            print(Exception)
            print("File already Removed")
