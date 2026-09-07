from django.urls import include, path
from rest_framework import routers

from books import viewsets

router = routers.SimpleRouter()
router.register(r"book", viewsets.BookViewSet, basename="book")
router.register(r"trade-request", viewsets.TradeRequestViewSet, basename="trade-request")
router.register(r"book-comment", viewsets.BookCommentViewSet, basename="book-comment")

urlpatterns = [
    path("", include(router.urls)),
]
