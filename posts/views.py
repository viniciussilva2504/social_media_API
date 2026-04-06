from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef

from posts.models import Post, Like, Comment
from accounts.models import Follow


@login_required
def feed_view(request):
    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list("following_id", flat=True)

    # Include own posts in feed
    feed_user_ids = list(following_ids) + [request.user.id]
    posts = (
        Post.objects.filter(author_id__in=feed_user_ids, is_active=True)
        .select_related("author", "author__profile")
        .annotate(
            _likes_count=Count("likes", distinct=True),
            _comments_count=Count("comments", distinct=True),
            _is_liked=Exists(
                Like.objects.filter(user=request.user, post=OuterRef("pk"))
            ),
        )
        .order_by("-created_at")
    )

    paginator = Paginator(posts, 20)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "feed.html", {
        "posts": page,
        "liked_post_ids": {p.pk for p in page if getattr(p, "_is_liked", False)},
    })


@login_required
def post_detail_view(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author", "author__profile"),
        id=post_id,
        is_active=True,
    )
    comments = post.comments.select_related("author", "author__profile").all()
    is_liked = Like.objects.filter(user=request.user, post=post).exists()

    if request.method == "POST":
        comment_content = request.POST.get("content", "").strip()
        if comment_content:
            Comment.objects.create(
                author=request.user,
                post=post,
                content=comment_content,
            )
            return redirect("post_detail", post_id=post.id)
        else:
            messages.error(request, "Comment cannot be empty.")

    return render(request, "post_detail.html", {
        "post": post,
        "comments": comments,
        "is_liked": is_liked,
    })


@login_required
def create_post_view(request):
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Post.objects.create(author=request.user, content=content)
            return redirect("feed")
        else:
            messages.error(request, "Post cannot be empty.")
    return render(request, "create_post.html")


@login_required
def search_view(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.none()
    if query:
        users = User.objects.filter(
            username__icontains=query
        ).select_related("profile").order_by("username")

    paginator = Paginator(users, 20)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "search.html", {"users": page, "query": query})
