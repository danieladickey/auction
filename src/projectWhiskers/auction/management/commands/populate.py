from django.core.management.base import BaseCommand, CommandError
from auction.models import *
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import make_aware

import shutil
import os
import datetime
import pytz


class Command(BaseCommand):
    help = 'Populates the database for testing.'
    numItems = 10
    numUsers = 10
    year = 3005

    def handle(self, *args, **options):
        self.createAuction(self.year)
        self.createItemBatch(self.numItems, self.year)
        self.createUserBatch(self.numUsers, self.year)

    def createAuction(self, year):
        settings.TIME_ZONE
        startTime = make_aware(datetime.datetime.now())
        endTime = make_aware(datetime.datetime.now() + datetime.timedelta(seconds=2*60*60))
        auction = Auction(year=year, startTime = startTime, endTime = endTime)
        auction.save()

    def createItemBatch(self, numItems, year):
        src = 'auction/static/auction/images/'
        dst = 'media/auction/'
        if not (os.path.exists(dst)):
            os.makedirs(dst)
        shutil.copy(src+'forsale.jpg', dst)
        shutil.copy(src+'testPicture.jpg', dst)
        auction = Auction.objects.get(year=year)
        for i in range(numItems - 8):
            silentItem = SilentItem(
                expiration=datetime.datetime(2020, 1, 1, 0, 0, 0, 0, tzinfo=pytz.UTC),
                name='item'+str(i),
                currentPrice=5*i,
                startingPrice=5*i,
                description="item description number "+str(i),
                photo='auction/forsale.jpg',
                itemType="silent")
            silentItem.save()

            liveItem = LiveItem(
                positionInAuction=LiveItem.objects.all().count() + 1,
                name='item' + str(i),
                currentPrice=5 * i,
                startingPrice=5 * i,
                description="item description number " + str(i),
                photo='auction/forsale.jpg',
                itemType="live")
            liveItem.save()
            auction.silentItems.add(silentItem)
            auction.liveItems.add(liveItem)

        for i in range(numItems):
            silentItem = SilentItem(
            expiration=datetime.datetime(2020, 1, 1, 0, 0, 0, 0, tzinfo=pytz.UTC),
            name='item'+str(i),
            currentPrice=5*i,
            startingPrice=5*i,
            description="item description number "+str(i),
            photo='auction/testPicture.jpg',
            itemType="silent")
            silentItem.save()

            liveItem = LiveItem(
            positionInAuction=LiveItem.objects.all().count() + 1,
            name='item' + str(i),
            currentPrice=5 * i,
            startingPrice=5 * i,
            description="item description number " + str(i),
            photo='auction/testPicture.jpg',
            itemType="live")
            liveItem.save()

            auction.silentItems.add(silentItem)
            auction.liveItems.add(liveItem)

        auction.save()


    def createUserBatch(self, numUsers, auctionYear):
        auction = Auction.objects.get(year=auctionYear)
        
        managerUser = User.objects.create_user('manager', password='test')
        managerUser.is_staff = True
        managerUser.save()
        
        manager = Manager(user=managerUser)
        manager.save()
        
        bidderManager = Bidder(user=managerUser)
        bidderManager.save()

        auction.participants.add(bidderManager)
        for i in range(numUsers):
            user = User.objects.create_user('user'+str(i), password='test')
            user.save()
            
            bidder = Bidder(user=user)
            bidder.save()
            
            auction.participants.add(bidder)

        auction.save()