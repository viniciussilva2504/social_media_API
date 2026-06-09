from django.urls import include, path
from rest_framework import routers

from books import viewsets

router = routers.SimpleRouter()
router.register(r"book", viewsets.BookViewSet, basename="book")
router.register(r"trade-request", viewsets.TradeRequestViewSet, basename="trade-request")

urlpatterns = [
    path("", include(router.urls)),
]
