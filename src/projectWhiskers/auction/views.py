from django.contrib.auth import get_user_model, authenticate, login, decorators
from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView
from .models import Item, SilentItem, LiveItem, Manager, Auction, Bidder
from django.conf import settings
from django.utils.timezone import make_aware
from django.views.decorators.cache import cache_control
import datetime
import pytz


# Create your views here.
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def user(request):
    checkExpired()
    try:
        notifications = request.user.bidder.notifications.order_by('-timeReceived')
        isUser = True
        return render(request, 'auction/user.html', {'notifications': notifications, 'isUser': isUser})
    except Exception:
        return redirect('/')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def liveItemWinner(request):
    checkExpired()

    auction = Auction.objects.all()
    return render(request, 'auction/liveItemWinner.html', {'items':LiveItem.objects.filter(sold=False), 'auctions':auction})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def makeLiveItemWinner(request, itemID):
    if request.method == "POST":
        winningBid = float(request.POST['price'])
        user1 = int(request.POST['userID'])

    user1 = get_object_or_404(Bidder, id=user1)
    item = get_object_or_404(LiveItem, id=itemID)

    item.currentPrice = winningBid
    item.winner = user1
    item.sold = True
    item.save()

    user1.liveItemsWon.add(item)
    item.notifyUser(message=f'Congratulations, you have won {item.name} for the price of $%.2f.' % item.currentPrice, user=item.winner)
    item.save()

    return HttpResponseRedirect(reverse('auction:liveItemWinner'))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def myWinning(request):
    checkExpired()
    currentTotal = 0
    for item in request.user.bidder.winning.all():
        currentTotal += item.currentPrice
    return render(request, 'auction/myWinning.html', {'total': currentTotal})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def myWon(request):
    checkExpired()
    silentTotal = 0
    liveTotal = 0
    for item in request.user.bidder.itemsWon.all():
        silentTotal += item.currentPrice
    for item in request.user.bidder.liveItemsWon.all():
        liveTotal += item.currentPrice
    total = silentTotal + liveTotal
    return render(request, 'auction/myWon.html', {'silentTotal': silentTotal, 'liveTotal': liveTotal, 'total': total})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def myBidding(request):
    checkExpired()	
    return render(request, 'auction/myBidding.html', {})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def manager(request):
    checkExpired()
    try:
        manager = request.user.manager
        auction = Auction.objects.all()
        return render(request, 'auction/manager.html', {'auction': auction})
    except Exception:
        print("a nonmanager tried to access the main manager page")
        return redirect('/user/')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def addItem(request):
    checkExpired()
    try:
        manager = request.user.manager
    except Exception:
        print("a nonmanager tried to access the addItem page")
        return redirect('/user/')
    else:
        if request.method == 'POST':
            try:
                itemName = request.POST['itemName']
                startPrice = request.POST['startingPrice']
                auctionType = request.POST['auctionType']
                description = request.POST['description']
                keywords = request.POST['keywords']
                whichAuction = request.POST['auction']
                photoData = request.FILES['photo']
                if auctionType and itemName and startPrice and description:
                    thisAuction = get_object_or_404(Auction, id=whichAuction)
                    if auctionType == "silent":
                        newItem = SilentItem(
                            expiration=thisAuction.endTime,
                            name=itemName,
                            startingPrice=startPrice,
                            currentPrice=startPrice,
                            description=description,
                            photo=SimpleUploadedFile(photoData.name, photoData.read()),
                            itemType=auctionType
                        )
                    if auctionType == "live":
                        newItem = LiveItem(
                            positionInAuction=LiveItem.objects.all().count() + 1,
                            name=itemName,
                            startingPrice=startPrice,
                            currentPrice=startPrice,
                            description=description,
                            photo=SimpleUploadedFile(photoData.name, photoData.read()),
                            itemType=auctionType,
                        )
                else:
                    auction = Auction.objects.all()
                    return render(request, 'auction/addItem.html', {
                        'messageItem': 'Please fill out all data fields.', 'auction': auction
                    })
            except KeyError:
                auction = Auction.objects.all()
                return render(request, 'auction/addItem.html', {
                    'messageItem': 'KeyError. Please fill out all data fields.', 'auction': auction
                })
            else:
                newItem.save()
                if auctionType == "silent":
                    thisAuction.silentItems.add(newItem)
                if auctionType == "live":
                    thisAuction.liveItems.add(newItem)
                thisAuction.save()
                return HttpResponseRedirect(reverse('auction:addItem'))
        else:
            auction = Auction.objects.all()
            return render(request, 'auction/addItem.html', {'auction': auction})


def addAdmin(request):
    pass

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def addBidder(request):
    checkExpired()
    try:
        manager = request.user.manager
    except Exception:
        print("A nonmanager tried to access the addBidder page")
        return redirect('/user/')
    else:
        if request.method == 'POST':
            try:
                username = request.POST['username']
                auctionName = request.POST['auctionName']
                if username and auctionName:
                    newBidder = Bidder(
                        user=get_user_model().objects.get(username=username),
                        auctionLocation=auctionName,
                    )
                else:
                    return render(request, 'auction/addBidder.html', {
                        'messageUser:': 'Please fill out all data fields.',
                    })
            except KeyError:
                return render(request, 'auction/addBidder.html', {
                    'messageUser:': 'KeyError. Please fill out all data fields.',
                })
            else:
                newBidder.save()
                editAuction = get_object_or_404(Auction, auctionName=auctionName.split(',')[0])
                editAuction.participants.add(newBidder)
                editAuction.save()
                return HttpResponseRedirect(reverse('auction:addBidder'))
        else:
            auction = Auction.objects.all()
            return render(request, 'auction/addBidder.html', {'auction': auction})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def removeBidder(request):
    checkExpired()
    try:
        manager = request.user.manager
    except Exception:
        print("A nonmanager tried to access the removeBidder page")
        return redirect('/user/')
    else:
        bidder = Bidder.objects.all()
        return render(request, 'auction/removeBidder.html', {'bidder': bidder})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def removeBidderFin(request, user_id):
    checkExpired()
    try:
        manager = request.user.manager
    except Exception:
        print("A nonmanager tried to access the removeBidderFin page")
        return redirect('/user/')
    else:
        bidder = get_object_or_404(Bidder, pk=user_id)
        bidder.delete()
        return HttpResponseRedirect(reverse('auction:removeBidder'))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def addAuction(request):
    checkExpired()
    try:
        manager = request.user.manager
    except Exception:
        print("A nonmanager tried to access the addAuction page")
        return redirect('/user/')
    else:
        if request.method == 'POST':
            try:
                newAuctionName = request.POST['auctionName']
                startDateRaw = request.POST['startDate']
                startTimeRaw = request.POST['startTime']
                endDateRaw = request.POST['endDate']
                endTimeRaw = request.POST['endTime']
                if newAuctionName:
                    settings.TIME_ZONE
                    currentTime = make_aware(datetime.time())
                    currentDate = datetime.date.today()
                    if startDateRaw and startDateRaw > currentDate.strftime('%YYYY-%MM-%DD'):
                        startDate = list(map(int, startDateRaw.split('-')))
                    else:
                        startDate = [currentDate.year, currentDate.month, currentDate.day]
                    if startTimeRaw:
                        startTime = list(map(int, startTimeRaw.split(':')))
                    else:
                        startTime = [currentTime.hour, currentTime.minute]
                    if endDateRaw and endDateRaw > startDateRaw:
                        endDate = list(map(int, endDateRaw.split('-')))
                    else:
                        endDate = [startDate[0], startDate[1], startDate[2]]
                    if endTimeRaw:
                        endTime = list(map(int, endTimeRaw.split(':')))
                    else:
                        endTime = [startTime[0]+2, startTime[1]]

                    newAuction = Auction(
                        startTime = make_aware(datetime.datetime(startDate[0], startDate[1], startDate[2], startTime[0], startTime[1], 0, 0)),
                        endTime = make_aware(datetime.datetime(endDate[0], endDate[1], endDate[2], endTime[0], endTime[1], 0, 0)),
                        auctionName = newAuctionName,
                        year = startDate[0]
                    )
                    pass
                else:
                    return render(request, 'auction/addAuction.html', {
                        'messageUser:': 'Please fill out all data fields.',
                    })
            except KeyError:
                return render(request, 'auction/addAuction.html', {
                    'messageUser:': 'KeyError. Please fill out all data fields.',
                })
            else:
                newAuction.save()
                return HttpResponseRedirect(reverse('auction:addAuction'))
        else:
            return render(request, 'auction/addAuction.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def endAuction(request):
    checkExpired()
    try:
        manager = request.user.manager
    except Exception:
        print("a nonmanager tried to access the endAuction page")
        return redirect('/user/')
    else:
        auction = request.POST['auction']
        removeAuction = get_object_or_404(Auction, id=auction)
        endTime = removeAuction.endTime
        items = removeAuction.silentItems.all()
        for item in items:
            item.manualExpire()
        return HttpResponseRedirect(reverse('auction:manager'))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def report(request):
    checkExpired()
    try:
        manager = request.user.manager
    except Exception:
        print("a nonmanager tried to access the report page")
        return redirect('/user/')
    else:
        auction = request.POST['auction']
        auctionToReport = get_object_or_404(Auction, id=auction)
        auctionToReport.makeReport()
        silentSoldFor = 0
        liveSoldFor = 0
        for silent in auctionToReport.silentItems.all():
            if silent.currentPrice > silent.startingPrice and silent.sold:
                silentSoldFor += silent.currentPrice
        for live in auctionToReport.liveItems.all():
            if live.currentPrice > live.startingPrice and live.sold:
                liveSoldFor += live.currentPrice
        totalSoldFor = silentSoldFor + liveSoldFor
        return render(request, 'auction/report.html', {'auction': auctionToReport, 'silent': silentSoldFor, 'live': liveSoldFor, 'total': totalSoldFor})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def allItems(request, price, numberOfItems):
    checkExpired()
    settings.TIME_ZONE
    now = make_aware(datetime.datetime.now())
    silentItems = SilentItem.objects.filter(expiration__gte=now)
    liveItems = LiveItem.objects.all()

    if request.method == "POST":
        if request.POST['auctionType'] == 'all':
            filterData = filterPage(silentItems, liveItems,request.POST['priceFilter'],request.POST['numberOfItems'])
            return render(request, 'auction/allItems.html', {'silent': filterData['silent'], 'live': filterData['live']})
        elif request.POST['auctionType'] == 'live':
            return HttpResponseRedirect(reverse('auction:liveItem',args=[request.POST['priceFilter'],request.POST['numberOfItems']]))
        elif request.POST['auctionType'] == 'silent':
            return HttpResponseRedirect(reverse('auction:silentItem',args=[request.POST['priceFilter'],request.POST['numberOfItems']]))
    else:
        filterData = filterPage(silentItems, liveItems,price,numberOfItems)
        return render(request, 'auction/allItems.html', {'silent': filterData['silent'], 'live': filterData['live']})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def newBid(request, item_id, page):
    checkExpired()
    item = get_object_or_404(SilentItem, pk=item_id)
    user = request.user

    user.bidder.make_bid(float(request.POST['bid']), item)

    silentItems = SilentItem.objects.all()

    if page == 'viewItemPage':
        return HttpResponseRedirect(reverse('auction:viewItem', args=(item_id, 'silent')))
    else:
        return HttpResponseRedirect(reverse('auction:silentItem'))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def viewItem(request, item_id, item_type):
    checkExpired()
    if item_type == 'live':
        item = get_object_or_404(LiveItem, pk=item_id)
        checkTime = False

    if item_type == 'silent':
        item = get_object_or_404(SilentItem, pk=item_id)
        settings.TIME_ZONE
        checkTime = not item.sold
    return render(request, 'auction/viewItem.html', {'item': item, 'timeOut': checkTime})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def liveItem(request, price, numberOfItems):
    checkExpired()
    settings.TIME_ZONE
    now = make_aware(datetime.datetime.now())
    silentItems = SilentItem.objects.filter(expiration__gte=now)
    liveItems = LiveItem.objects.all()

    if request.method == "POST":
        if request.POST['auctionType'] == 'all':
            return HttpResponseRedirect(reverse('auction:allItems',args=[request.POST['priceFilter'],request.POST['numberOfItems']]))
        elif request.POST['auctionType'] == 'live':
            filterData = filterPage(silentItems, liveItems, request.POST['priceFilter'],request.POST['numberOfItems'])
            return render(request, 'auction/liveItem.html', {'items': filterData['live']})
        elif request.POST['auctionType'] == 'silent':
            return HttpResponseRedirect(reverse('auction:silentItem',args=[request.POST['priceFilter'],request.POST['numberOfItems']]))
    else:
        filterData = filterPage(silentItems, liveItems, price, numberOfItems)
        return render(request, 'auction/liveItem.html', {'items': filterData['live']})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def silentItem(request, price, numberOfItems):
    checkExpired()
    settings.TIME_ZONE
    now = make_aware(datetime.datetime.now())
    silentItems = SilentItem.objects.filter(expiration__gte=now)
    liveItems = LiveItem.objects.all()

    if request.method == "POST":
        if request.POST['auctionType'] == 'all':
            return HttpResponseRedirect(reverse('auction:allItems',args=[request.POST['priceFilter'],request.POST['numberOfItems']]))
        elif request.POST['auctionType'] == 'live':
            return HttpResponseRedirect(reverse('auction:liveItem',args=[request.POST['priceFilter'],request.POST['numberOfItems']]))
        elif request.POST['auctionType'] == 'silent':
            filterData = filterPage(silentItems, liveItems, request.POST['priceFilter'],request.POST['numberOfItems'])
            return render(request, 'auction/silentItem.html', {'items': filterData['silent']})
    else:
        filterData = filterPage(silentItems, liveItems, price, numberOfItems)
        return render(request, 'auction/silentItem.html', {'items': filterData['silent']})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    checkExpired()
    return render(request, 'auction/home.html', {})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def contact(request):
    checkExpired()
    return render(request, 'auction/contact.html', {})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@decorators.login_required()
def id(request):
    checkExpired()
    return render(request, 'auction/id.html', {})


def filterPage(silentItems, liveItems, price, number):
    priceFilter = int(price)
    numberOfItems = int(number)

    if numberOfItems == 0 and priceFilter == 0:
        return {'silent': silentItems, 'live': liveItems}
    elif numberOfItems != 0 and priceFilter == 0:
        return {'silent': silentItems.order_by()[:numberOfItems], 'live': liveItems.order_by()[:numberOfItems]}
    else:
        tmpSilent = filterPrice(silentItems, liveItems, priceFilter, numberOfItems)['silent']
        tmpLive = filterPrice(silentItems, liveItems, priceFilter, numberOfItems)['live']
        return {'silent': tmpSilent, 'live': tmpLive, }


def filterPrice(silentItems, liveItems, priceFilter, numberOfItems):
    tempSilent = []
    tempLive = []

    checkExpired()
    settings.TIME_ZONE
    now = make_aware(datetime.datetime.now())
    silentItemsExpired = SilentItem.objects.filter(expiration__gte=now)

    if priceFilter == 9:
        for i in silentItems:
            if i.currentPrice < 10:
                tempSilent.append(i)
            if len(tempSilent) >= numberOfItems and numberOfItems != 0:
                break
        for i in liveItems:
            if i.currentPrice < 10:
                tempLive.append(i)
            if len(tempLive) >= numberOfItems and numberOfItems != 0:
                break
        return {'silent': tempSilent, 'live': tempLive}
    elif priceFilter == 10:
        for i in silentItems:
            if i.currentPrice >= 10 and i.currentPrice < 50:
                tempSilent.append(i)
            if len(tempSilent) >= numberOfItems and numberOfItems != 0:
                break
        for i in liveItems:
            if i.currentPrice >= 10 and i.currentPrice < 50:
                tempLive.append(i)
            if len(tempLive) >= numberOfItems and numberOfItems != 0:
                break
        return {'silent': tempSilent, 'live': tempLive}
    elif priceFilter == 50:
        for i in silentItems:
            if i.currentPrice >= 50 and i.currentPrice < 100:
                tempSilent.append(i)
            if len(tempSilent) >= numberOfItems and numberOfItems != 0:
                break
        for i in liveItems:
            if i.currentPrice >= 50 and i.currentPrice < 100:
                tempLive.append(i)
            if len(tempLive) >= numberOfItems and numberOfItems != 0:
                break
        return {'silent': tempSilent, 'live': tempLive}
    elif priceFilter == 100:
        for i in silentItems:
            if i.currentPrice >= 100 and i.currentPrice < 1000:
                tempSilent.append(i)
            if len(tempSilent) >= numberOfItems and numberOfItems != 0:
                break
        for i in liveItems:
            if i.currentPrice >= 100 and i.currentPrice < 1000:
                tempLive.append(i)
            if len(tempLive) >= numberOfItems and numberOfItems != 0:
                break
        return {'silent': tempSilent, 'live': tempLive}
    elif priceFilter == 101:
        for i in silentItems:
            if i.currentPrice >= 1000:
                tempSilent.append(i)
            if len(tempSilent) >= numberOfItems and numberOfItems != 0:
                break
        for i in liveItems:
            if i.currentPrice >= 1000:
                tempLive.append(i)
            if len(tempLive) >= numberOfItems and numberOfItems != 0:
                break
        return {'silent': tempSilent, 'live': tempLive}

class SignUp(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('auction:home')
    template_name = 'registration/signup.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['auction'] = Auction.objects.all()
        return context

    def form_valid(self, form):
        checkExpired()
        to_return = super().form_valid(form)
        login(self.request, self.object)
        return to_return

    def post(self, request):
        to_return = super().post(self, request)
        try:
            auction = get_object_or_404(Auction, id=request.POST.get('auction'))
        except Exception:
            pass
        else:
            newBidder = Bidder(
                user=get_user_model().objects.get(username=request.POST.get('username')),
                auctionLocation=auction.auctionName,
            )
            newBidder.save()
            auction.participants.add(newBidder)
            auction.save()

        return to_return

# checks the expiration on all items that expire within the next 60 seconds, 
# rather than all items, because that could slow things down
def checkExpired():
	settings.TIME_ZONE
	future = make_aware(datetime.datetime.now() + datetime.timedelta(seconds=60))
	items = SilentItem.objects.filter(expiration__lte=future, sold=False)

	for item in items:
		item.expire()