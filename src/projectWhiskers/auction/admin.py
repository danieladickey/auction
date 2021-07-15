from django.contrib import admin
from .models import Manager, Item, SilentItem, LiveItem, Auction, Bidder

# Register your models here.
admin.site.register(Manager)
admin.site.register(SilentItem)
admin.site.register(LiveItem)
admin.site.register(Auction)
admin.site.register(Bidder)
