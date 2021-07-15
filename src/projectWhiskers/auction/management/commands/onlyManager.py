from django.core.management.base import BaseCommand, CommandError
from auction.models import *
from django.contrib.auth.models import User
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = 'Populates the database with a single manager'

    def handle(self, *args, **kwargs):
        call_command('reset')
        call_command('makemigrations')
        call_command('migrate')
        self.createManager()

    def createManager(self):
        dst = 'media/auction/'
        if not (os.path.exists(dst)):
            os.makedirs(dst)

        managerUser = User.objects.create_user('manager', password='test')
        managerUser.save()
        managerUser.is_staff = True
        
        manager = Manager(user=managerUser)
        manager.save()
        
        # bidderManager = Bidder(user=managerUser)
        # bidderManager.save()
