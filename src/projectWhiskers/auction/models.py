from django.db import models
from django.contrib.auth import get_user_model, decorators
from django.conf import settings
from django.utils.timezone import make_aware
import datetime


class Item(models.Model):
    name = models.CharField(max_length=100, default='')
    currentPrice = models.DecimalField(default=0, max_digits=60, decimal_places=2)
    startingPrice = models.DecimalField(default=0, max_digits=60, decimal_places=2)
    description = models.TextField(blank=True)
    photo = models.ImageField(blank=True, upload_to="auction/")
    itemType = models.TextField(blank=True)
    sold = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.name} - ${self.currentPrice}'

    def notifyAdmin(self, message):
        # send the admin a message relating to if an item is sold
        pass


class SilentItem(Item):
    expiration = models.DateTimeField(blank=True)
    bidders = models.ManyToManyField('auction.Bidder', blank=True, related_name='itemsBidOn')
    userWinning = models.ForeignKey('auction.Bidder', blank=True, null=True, on_delete=models.SET_NULL, related_name='winning')
    bidWinning = models.OneToOneField('auction.Bid', blank=True, null=True, on_delete=models.SET_NULL, related_name='winning')
    winner = models.ForeignKey('auction.Bidder', blank=True, null=True, on_delete=models.SET_NULL, related_name='itemsWon')

    def notifyUser(self, message, user):
        # send a user a message relating to item bid on
        settings.TIME_ZONE
        notification = Notification(message=message, user=user, item=self, timeReceived=make_aware(datetime.datetime.now()))
        notification.save()

    def expire(self):
        settings.TIME_ZONE
        now = make_aware(datetime.datetime.now())
        if (self.expiration <= now) and (not self.sold):
            self.manualExpire()

    def manualExpire(self):
        try:
            self.sold = True
            self.save()
            self.winner = self.userWinning
            self.notifyUser(message=f'Congratulations, you have won {self.name} for the price of ${self.bidWinning.bidPrice}.',
                            user=self.winner)
            for bidder in self.bidders.all():
                if bidder != self.winner:
                    self.notifyUser(message=f'The silent auction of {self.name} is over. Bids have been disallowed and the winner has been notified.', 
                                user=bidder)
            self.save()
        except Exception:
            print(f'Item {self.name} expired with no bidder.')

class LiveItem(Item):
    positionInAuction = models.PositiveSmallIntegerField(default=1)
    winner = models.ForeignKey('auction.Bidder', blank=True, null=True, on_delete=models.SET_NULL, related_name='liveItemsWon')

    def notifyUser(self, message, user):
        # send a user a message relating to item bid on
        settings.TIME_ZONE
        notification = Notification(message=message, user=user, liveItem=self, timeReceived=make_aware(datetime.datetime.now()))
        notification.save()

class Auction(models.Model):
    startTime = models.DateTimeField(blank=True)
    endTime = models.DateTimeField(blank=True)
    year = models.PositiveSmallIntegerField(default=2020)
    participants = models.ManyToManyField('auction.Bidder', related_name='auctions')
    auctionName = models.CharField(max_length=100, default='auction')
    silentItems = models.ManyToManyField('auction.SilentItem', related_name='silentItems')
    liveItems = models.ManyToManyField('auction.LiveItem', related_name='liveItems')

    def makeReport(self):
        # make a report for the auction's status, revenue, etc.
        pass

    def __str__(self):
        return f'{self.auctionName}, {self.participants.all().count()} participants'


class Bidder(models.Model):
    user = models.OneToOneField(get_user_model(), blank=False, on_delete=models.CASCADE, related_name='bidder')
    auctionLocation = models.CharField(max_length=100, default='')

    def make_bid(self, bid_price, item):
        settings.TIME_ZONE
        now = make_aware(datetime.datetime.now())
        if item.expiration > now and not item.sold:
            item.bidders.add(self)
            item.save()

            if bid_price > item.currentPrice:
                userToNotify = item.userWinning
                bid = Bid(bidPrice=bid_price, item=item, bidder=self)
                bid.save()
                item.currentPrice = bid_price
                item.bidWinning = bid
                item.userWinning = self
                item.save()
                # notify top bidder that they have been outbid
                if userToNotify and userToNotify.id != self.id:
                    item.notifyUser(message="Outbid on: " + str(item), user=userToNotify)
        else:
            # notify bidder that their bid couldn't go through
            item.notifyUser(message="This item has expired, bid could not be submitted.", user=self.user.bidder)

    def announcement(self, message):
        if self.user.is_staff:
            settings.TIME_ZONE
            for user in Bidder.objects.all():
                notification = Notification(message=message, user=user, item=None,
                                        timeReceived=make_aware(datetime.datetime.now()))
                notification.save()

    def __str__(self):
        return f'{self.user.username}'


class Bid(models.Model):
    bidPrice = models.DecimalField(default=0.0, max_digits=60, decimal_places=2)
    item = models.ForeignKey(SilentItem, blank=False, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(Bidder, blank=False, on_delete=models.CASCADE, related_name='bids')

    def __str__(self):
        return f'{self.bidPrice} for {self.item}'

    def save(self, *args, **kwargs):
        self.bidPrice = round(self.bidPrice, 2)
        super(Bid, self).save(*args, **kwargs)

class Notification(models.Model):
    message = models.TextField(default='')
    read = models.BooleanField(default=False)
    timeReceived = models.DateTimeField(blank=False)
    item = models.ForeignKey(SilentItem, blank=True, null=True, on_delete=models.SET_NULL, related_name='notifications')
    liveItem = models.ForeignKey(LiveItem, blank=True, null=True, on_delete=models.SET_NULL, related_name='liveNotifications')
    user = models.ForeignKey(Bidder, blank=False, on_delete=models.CASCADE, related_name='notifications')

    def __str__(self):
        return f'{self.message}'


class Manager(models.Model):
    user = models.OneToOneField(get_user_model(), blank=False, on_delete=models.CASCADE, related_name='manager')

    def __str__(self):
        return f'{self.user.username}'
