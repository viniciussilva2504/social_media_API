from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef

from posts.models import Post, Like, Comment

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


@login_required
def feed_view(request):
    posts = (
        Post.objects.filter(is_active=True)
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
            if len(comment_content) > 50:
                messages.error(request, "Comment must be at most 50 characters.")
                return render(request, "post_detail.html", {
                    "post": post,
                    "comments": comments,
                    "is_liked": is_liked,
                    "is_owner": request.user == post.author,
                })
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
        "is_owner": request.user == post.author,
    })


@login_required
def edit_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, is_active=True)
    if request.user != post.author:
        return redirect("post_detail", post_id=post.id)

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        image = request.FILES.get("image")
        remove_image = request.POST.get("remove_image") == "1"
        if content:
            post.content = content
            update_fields = ["content", "updated_at"]
            if remove_image:
                post.image = None
                update_fields.append("image")
            elif image:
                if image.content_type not in ALLOWED_IMAGE_TYPES:
                    messages.error(request, "Only JPEG, PNG, and WebP images are allowed.")
                    return render(request, "edit_post.html", {"post": post})
                if image.size > MAX_IMAGE_SIZE:
                    messages.error(request, "Image must be under 5MB.")
                    return render(request, "edit_post.html", {"post": post})
                post.image = image
                update_fields.append("image")
            post.save(update_fields=update_fields)
            messages.success(request, "Post updated.")
            return redirect("post_detail", post_id=post.id)
        else:
            messages.error(request, "Post cannot be empty.")

    return render(request, "edit_post.html", {"post": post})


@login_required
def delete_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, is_active=True)
    if request.user != post.author:
        return redirect("post_detail", post_id=post.id)

    if request.method == "POST":
        post.is_active = False
        post.save(update_fields=["is_active"])
        messages.success(request, "Post deleted.")
        return redirect("feed")

    return render(request, "post_detail.html", {
        "post": post,
        "comments": post.comments.select_related("author", "author__profile").all(),
        "is_liked": Like.objects.filter(user=request.user, post=post).exists(),
        "is_owner": True,
    })


@login_required
def create_post_view(request):
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        image = request.FILES.get("image")
        if content:
            if image:
                if image.content_type not in ALLOWED_IMAGE_TYPES:
                    messages.error(request, "Only JPEG, PNG, and WebP images are allowed.")
                    return render(request, "create_post.html")
                if image.size > MAX_IMAGE_SIZE:
                    messages.error(request, "Image must be under 5MB.")
                    return render(request, "create_post.html")
            Post.objects.create(author=request.user, content=content, image=image)
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
