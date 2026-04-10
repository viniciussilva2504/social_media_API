from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count, Exists, OuterRef

from accounts.models import Profile, Follow
from posts.models import Like

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB


def home_view(request):
    if request.user.is_authenticated:
        return redirect("feed")
    return render(request, "home.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, "register.html")

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, "register.html")

        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "register.html")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("feed")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("feed")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "login.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")
    return redirect("home")


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    posts = (
        user.posts.filter(is_active=True)
        .annotate(
            _likes_count=Count("likes", distinct=True),
            _comments_count=Count("comments", distinct=True),
            _is_liked=Exists(
                Like.objects.filter(user=request.user, post=OuterRef("pk"))
            ),
        )
        .order_by("-created_at")
    )
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    is_own_profile = request.user == user

    paginator = Paginator(posts, 20)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "profile.html", {
        "profile_user": user,
        "profile": profile,
        "posts": page,
        "is_following": is_following,
        "is_own_profile": is_own_profile,
    })


@login_required
def edit_profile_view(request, username):
    if request.user.username != username:
        return redirect("profile", username=username)

    profile = request.user.profile

    if request.method == "POST":
        display_name = request.POST.get("display_name", "").strip()
        bio = request.POST.get("bio", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        profile_picture = request.FILES.get("profile_picture")

        if display_name:
            profile.display_name = display_name
        if bio is not None:
            profile.bio = bio
        if profile_picture:
            if profile_picture.content_type not in ALLOWED_IMAGE_TYPES:
                messages.error(request, "Only JPEG, PNG, and WebP images are allowed.")
                return render(request, "edit_profile.html", {"profile": profile})
            if profile_picture.size > MAX_UPLOAD_SIZE:
                messages.error(request, "Image must be under 5MB.")
                return render(request, "edit_profile.html", {"profile": profile})
            profile.profile_picture = profile_picture
        if new_password:
            try:
                validate_password(new_password, request.user)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return render(request, "edit_profile.html", {"profile": profile})
            request.user.set_password(new_password)
            request.user.save()
            login(request, request.user)

        profile.save()
        messages.success(request, "Profile updated.")
        return redirect("profile", username=username)

    return render(request, "edit_profile.html", {"profile": profile})


@login_required
def followers_view(request, username):
    user = get_object_or_404(User, username=username)
    follower_ids = Follow.objects.filter(following=user).values_list("follower_id", flat=True)
    followers = User.objects.filter(id__in=follower_ids).select_related("profile").order_by("username")
    paginator = Paginator(followers, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "follow_list.html", {
        "profile_user": user,
        "users": page,
        "list_type": "Followers",
    })


@login_required
def following_view(request, username):
    user = get_object_or_404(User, username=username)
    following_ids = Follow.objects.filter(follower=user).values_list("following_id", flat=True)
    following = User.objects.filter(id__in=following_ids).select_related("profile").order_by("username")
    paginator = Paginator(following, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "follow_list.html", {
        "profile_user": user,
        "users": page,
        "list_type": "Following",
    })
