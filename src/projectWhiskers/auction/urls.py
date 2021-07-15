from django.urls import path
from . import views


app_name = 'auction'
urlpatterns = [
	path('', views.home, name='home'),
	path('user/', views.user, name='user'),
	path('user/mybidding/', views.myBidding, name='myBidding'),
	path('user/mywinning/', views.myWinning, name='myWinning'),
	path('user/mywon/', views.myWon, name='myWon'),
	path('manager/', views.manager, name='manager'),
	path('manager/addbidder/', views.addBidder, name="addBidder"),
	path('manager/removebidder/', views.removeBidder, name="removeBidder"),
	path('manager/removebidder/<int:user_id>/', views.removeBidderFin, name="removeBidderFin"),
	path('manager/additem/', views.addItem, name="addItem"),
	path('manager/addauction/', views.addAuction, name="addAuction"),
	path('manager/endauction/', views.endAuction, name="endAuction"),
	path('manager/report/', views.report, name="report"),
	path('allitems/<int:price>/<int:numberOfItems>/',views.allItems, name ='allItems'),
	path('liveitem/<int:price>/<int:numberOfItems>/', views.liveItem, name='liveItem'),
	path('silentitem/<int:price>/<int:numberOfItems>/', views.silentItem, name='silentItem'),
	path('contact/', views.contact, name='contact'),
	path('id/', views.id, name='id'),
	path('newbid/<int:item_id>/<slug:page>/', views.newBid, name = 'newBid'),
	path('viewitem/<int:item_id>/<slug:item_type>/', views.viewItem, name='viewItem'),
	path('signup/', views.SignUp.as_view(), name='signup'),
	path('manager/liveitemwinner/', views.liveItemWinner, name='liveItemWinner'),
	path('makeliveitemwinner/<int:itemID>', views.makeLiveItemWinner, name='makeLiveItemWinner'),
]
