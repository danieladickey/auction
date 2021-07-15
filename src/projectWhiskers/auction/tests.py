from django.contrib.auth.models import User
from django.test import TestCase
from django.conf import settings
from django.utils.timezone import make_aware
from auction.models import *

import datetime


class FirstBidTestCase(TestCase):
    def setUp(self):
        settings.TIME_ZONE
        currentTime = make_aware(datetime.datetime.now())
        endTime = make_aware(datetime.datetime.now() + datetime.timedelta(hours=2))
        auction = Auction(auctionName="default", startTime=currentTime, endTime=endTime)
        auction.save()

        SilentItem.objects.create(name="boomerang", currentPrice=10.00, startingPrice=10.00,
                                  description="this is a boomerang", expiration=auction.endTime)
        # create bidders for testing the bid on the boomerang
        User.objects.create_user(username='iwilloutbid', password='thisisatest')
        Bidder.objects.create(user=User.objects.get(username='iwilloutbid'))
        auction.participants.add(Bidder.objects.get(user=User.objects.get(username='iwilloutbid')))
        auction.silentItems.add(SilentItem.objects.get(name="boomerang"))
        auction.save()

    # Tests that a bid goes through
    def test_make_bid(self):
        boomerang = SilentItem.objects.get(name="boomerang")
        newWinner = User.objects.get(username='iwilloutbid').bidder

        self.assertEqual(boomerang.userWinning, None)
        self.assertEqual(boomerang.bidWinning, None)

        newWinner.make_bid(bid_price=15.00, item=boomerang)
        bid = Bid.objects.get(bidder=newWinner)
        self.assertNotEqual(bid, None)

        self.assertEqual(boomerang.currentPrice, 15.00)
        self.assertEqual(boomerang.userWinning, newWinner)
        self.assertEqual(boomerang.bidWinning, bid)


class OutbidTestCase(TestCase):
    def setUp(self):
        settings.TIME_ZONE
        currentTime = make_aware(datetime.datetime.now() + datetime.timedelta(hours=2))
        SilentItem.objects.create(name="boomerang", currentPrice=10.00, startingPrice=10.00,
                                  description="this is a boomerang", expiration=currentTime)
        # create bidders for testing the bid on the boomerang
        User.objects.create_user(username='iamwinning', password='thisisatest')
        Bidder.objects.create(user=User.objects.get(username='iamwinning'))
        User.objects.create_user(username='iwilloutbid', password='thisisatest')
        Bidder.objects.create(user=User.objects.get(username='iwilloutbid'))

    # Tests that a user gets notified when they are outbid
    def test_notify_user(self):
        boomerang = SilentItem.objects.get(name="boomerang")
        currentWinner = User.objects.get(username='iamwinning').bidder
        boomerang.userWinning = currentWinner
        boomerang.save()

        newWinner = User.objects.get(username='iwilloutbid').bidder
        newWinner.make_bid(bid_price=15.00, item=boomerang)
        notification = Notification.objects.get(user=currentWinner)
        self.assertIsNotNone(notification)

    # Tests that a new bid goes through
    def test_make_bid(self):
        boomerang = SilentItem.objects.get(name="boomerang")
        newWinner = User.objects.get(username='iwilloutbid').bidder

        self.assertIsNone(boomerang.userWinning)
        self.assertIsNone(boomerang.bidWinning)

        newWinner.make_bid(bid_price=15.00, item=boomerang)
        bid = Bid.objects.get(bidder=newWinner)
        self.assertIsNotNone(bid)

        self.assertEqual(boomerang.currentPrice, 15.00)
        self.assertEqual(boomerang.userWinning, newWinner)
        self.assertEqual(boomerang.bidWinning, bid)


class ExpireBidTestCase(TestCase):
    def setUp(self):
        currentTime = make_aware(datetime.datetime.now() - datetime.timedelta(hours=2))
        endTime = make_aware(datetime.datetime.now() + datetime.timedelta(seconds=60))
        auction = Auction(auctionName="default", startTime=currentTime, endTime=endTime)
        auction.save()

        SilentItem.objects.create(name="boomerang", currentPrice=10.00, startingPrice=10.00,
                                  description="this is a boomerang", expiration=auction.endTime)
        # create bidders for testing the bid on the boomerang
        User.objects.create_user(username='iwillbid', password='thisisatest')
        Bidder.objects.create(user=User.objects.get(username='iwillbid'))
        User.objects.create_user(username='iwillnotbid', password='thisisatest')
        Bidder.objects.create(user=User.objects.get(username='iwillnotbid'))

        auction.participants.add(User.objects.get(username='iwillbid').bidder)
        auction.participants.add(User.objects.get(username='iwillnotbid').bidder)
        auction.silentItems.add(SilentItem.objects.get(name="boomerang"))
        auction.save()

    # Tests that new bids do not go through when an item expires
    # Also gets items through Auction rather than through SilentItem
    def test_expire(self):
        auction = Auction.objects.get(auctionName='default')
        boomerang = auction.silentItems.get(name="boomerang")
        winner = auction.participants.get(user=User.objects.get(username='iwillbid'))
        notWinner = auction.participants.get(user=User.objects.get(username='iwillnotbid'))


        self.assertEqual(boomerang.userWinning, None)
        self.assertEqual(boomerang.bidWinning, None)
        self.assertEqual(boomerang.winner, None)
        self.assertEqual(boomerang.sold, False)

        winner.make_bid(bid_price=15.00, item=boomerang)

        winBid = Bid.objects.get(bidder=winner)
        self.assertNotEqual(winBid, None)
        self.assertEqual(boomerang.currentPrice, 15.00)
        self.assertEqual(boomerang.userWinning, winner)
        self.assertEqual(boomerang.bidWinning, winBid)

        boomerang.manualExpire()

        notWinner.make_bid(bid_price=16.00, item=boomerang)
        with self.assertRaises(Bid.DoesNotExist):
            Bid.objects.get(bidder=notWinner)

        self.assertEqual(boomerang.currentPrice, 15.00)
        self.assertEqual(boomerang.userWinning, winner)
        self.assertEqual(boomerang.bidWinning, winBid)
        self.assertEqual(boomerang.sold, True)


class GeneralTestCase(TestCase):
    def setUp(self):
        # create users to receive notifications
        for i in range(10):
            User.objects.create_user(username=str(i), password='thisisatest')
            Bidder.objects.create(user=User.objects.get(username=str(i)))
        # create admin
        User.objects.create_user(username='admin', password='thisisatest')
        user = User.objects.get(username='admin')
        user.is_staff = True
        user.save()
        Manager.objects.create(user=user)
        Bidder.objects.create(user=user)

    # Tests that managers can make announcements to all users
    def test_admin_announcement(self):
        user = User.objects.get(username='admin')
        bidder = Bidder.objects.get(user=user)
        bidder.announcement('EVERYBODY GET OUT NOW')

        for bidder in Bidder.objects.all():
            notifs = bidder.notifications.all()
            self.assertTrue(notifs)
            self.assertEqual(notifs[0].message, 'EVERYBODY GET OUT NOW')

    # Tests that non-managers cannot make announcements to all users
    def test_non_admin_announcement(self):
        user = User.objects.get(username='1')
        bidder = Bidder.objects.get(user=user)
        bidder.announcement('EVERYBODY GET OUT NOW')

        for bidder in Bidder.objects.all():
            notifs = bidder.notifications.all()
            self.assertFalse(notifs)

