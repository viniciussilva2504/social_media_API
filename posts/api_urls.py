from django.urls import include, path
from rest_framework import routers

from posts import viewsets

router = routers.SimpleRouter()
router.register(r"post", viewsets.PostViewSet, basename="post")
router.register(r"like", viewsets.LikeViewSet, basename="like")
router.register(r"comment", viewsets.CommentViewSet, basename="comment")
router.register(r"feed", viewsets.FeedViewSet, basename="feed")

urlpatterns = [
    path("", include(router.urls)),
]
