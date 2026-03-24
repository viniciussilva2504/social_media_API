from django.urls import path
from posts.views import feed_view, post_detail_view, create_post_view, search_view

urlpatterns = [
    path("feed/", feed_view, name="feed"),
    path("post/<int:post_id>/", post_detail_view, name="post_detail"),
    path("post/new/", create_post_view, name="create_post"),
    path("search/", search_view, name="search"),
]
