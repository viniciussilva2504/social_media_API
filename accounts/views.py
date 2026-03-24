from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from accounts.models import Profile, Follow


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

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "register.html")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
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
    logout(request)
    return redirect("home")


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    posts = user.posts.all().order_by("-created_at")
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    is_own_profile = request.user == user

    return render(request, "profile.html", {
        "profile_user": user,
        "profile": profile,
        "posts": posts,
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
            profile.profile_picture = profile_picture
        if new_password:
            if len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters.")
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
    followers = User.objects.filter(id__in=follower_ids).select_related("profile")
    return render(request, "follow_list.html", {
        "profile_user": user,
        "users": followers,
        "list_type": "Followers",
    })


@login_required
def following_view(request, username):
    user = get_object_or_404(User, username=username)
    following_ids = Follow.objects.filter(follower=user).values_list("following_id", flat=True)
    following = User.objects.filter(id__in=following_ids).select_related("profile")
    return render(request, "follow_list.html", {
        "profile_user": user,
        "users": following,
        "list_type": "Following",
    })
