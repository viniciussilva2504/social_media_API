import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from books.models.book import Book
from books.models.trade_request import TradeRequest
from books.models.book_comment import BookComment
from books.services.cover_fetch import fetch_cover_from_url, CoverFetchError
from books.services.url_import import import_book_metadata, BookImportError

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def biblioteca_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    books = (
        Book.objects.filter(owner=profile_user)
        .annotate(trade_requests_count=Count("trade_requests", distinct=True))
        .order_by("-created_at")
    )
    is_own = request.user.is_authenticated and request.user == profile_user
    return render(request, "biblioteca.html", {
        "profile_user": profile_user,
        "books": books,
        "is_own": is_own,
    })


@login_required
def add_book_view(request, username):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        book_author = request.POST.get("book_author", "").strip()
        description = request.POST.get("description", "").strip()
        cover = request.FILES.get("cover")
        cover_url = request.POST.get("cover_url", "").strip()

        # Re-render with whatever the user already typed on any error below,
        # so a validation failure never forces them to start the form over.
        form_data = {
            "title": title,
            "book_author": book_author,
            "description": description,
            "cover_url": cover_url,
        }

        if not title or not book_author:
            messages.error(request, "Title and author are required.")
            return render(request, "add_book.html", {"form_data": form_data})

        if len(title) > 200:
            messages.error(request, "Title must be at most 200 characters.")
            return render(request, "add_book.html", {"form_data": form_data})

        if len(book_author) > 200:
            messages.error(request, "Author must be at most 200 characters.")
            return render(request, "add_book.html", {"form_data": form_data})

        if len(description) > 500:
            messages.error(request, "Description must be at most 500 characters.")
            return render(request, "add_book.html", {"form_data": form_data})

        if not cover and not cover_url:
            messages.error(request, "Add a cover image or a cover image URL.")
            return render(request, "add_book.html", {"form_data": form_data})

        if cover:
            if cover.content_type not in ALLOWED_IMAGE_TYPES:
                messages.error(request, "Cover must be a JPG, PNG, or WebP image.")
                return render(request, "add_book.html", {"form_data": form_data})
            if cover.size > MAX_IMAGE_SIZE:
                messages.error(request, "Cover image must be under 5MB.")
                return render(request, "add_book.html", {"form_data": form_data})
        elif cover_url:
            try:
                cover = fetch_cover_from_url(cover_url)
            except CoverFetchError as e:
                messages.error(request, str(e))
                return render(request, "add_book.html", {"form_data": form_data})

        Book.objects.create(
            owner=request.user,
            title=title,
            book_author=book_author,
            description=description,
            cover=cover,
        )
        messages.success(request, "Book added to your biblioteca.")
        return redirect("biblioteca", username=request.user.username)

    return render(request, "add_book.html")


@login_required
@require_POST
def import_book_preview_view(request):
    """AJAX endpoint used by the "add a book" form: given a book/product
    page URL, returns best-effort title/author/description/cover-image-url
    extracted from its Open Graph / JSON-LD preview metadata, for the user
    to review before saving — nothing is persisted here.
    """
    try:
        payload = json.loads(request.body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid request."}, status=400)

    url = (payload.get("url") or "").strip()
    if not url:
        return JsonResponse({"ok": False, "error": "Paste a link first."}, status=400)

    try:
        data = import_book_metadata(url)
    except BookImportError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return JsonResponse({"ok": True, **data})


@login_required
def delete_book_view(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    if request.method == "POST":
        book.delete()
        messages.success(request, "Book removed from your biblioteca.")
    return redirect("biblioteca", username=request.user.username)


@login_required
@require_POST
def toggle_book_availability_view(request, book_id):
    """Lets the owner flip a book between available/unavailable for trade,
    without deleting it — e.g. to pause offers while deciding, or to
    reopen a book that was manually marked unavailable."""
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    book.is_available = not book.is_available
    book.save(update_fields=["is_available", "updated_at"])

    if book.is_available:
        messages.success(request, "Book marked as available for trade.")
    else:
        messages.success(request, "Book marked as unavailable.")

    return redirect("book_detail", book_id=book.id)


def book_detail_view(request, book_id):
    book = get_object_or_404(
        Book.objects.select_related("owner", "owner__profile"),
        id=book_id,
    )
    is_own = request.user.is_authenticated and request.user == book.owner

    pending_request = None
    if request.user.is_authenticated and not is_own:
        pending_request = TradeRequest.objects.filter(
            book=book, requester=request.user, status=TradeRequest.Status.PENDING
        ).first()

    trade_requests = []
    if is_own:
        trade_requests = book.trade_requests.select_related("requester").filter(
            status=TradeRequest.Status.PENDING
        ).order_by("-created_at")

    comments = book.comments.select_related("author", "author__profile").all()

    context = {
        "book": book,
        "is_own": is_own,
        "pending_request": pending_request,
        "trade_requests": trade_requests,
        "comments": comments,
    }

    if request.method == "POST" and request.user.is_authenticated:
        form_type = request.POST.get("form_type")

        if form_type == "comment":
            content = request.POST.get("content", "").strip()
            if not content:
                messages.error(request, "Comment cannot be empty.")
            elif len(content) > 280:
                messages.error(request, "Comment must be at most 280 characters.")
            else:
                BookComment.objects.create(author=request.user, book=book, content=content)
                return redirect("book_detail", book_id=book.id)
            return render(request, "book_detail.html", context)

        if form_type == "trade_request" and not is_own:
            if pending_request:
                messages.error(request, "You already have a pending trade request for this book.")
                return redirect("book_detail", book_id=book.id)

            offered_book = request.POST.get("offered_book", "").strip()
            message = request.POST.get("message", "").strip()

            if not offered_book:
                messages.error(request, "Please specify which book you want to offer.")
                return render(request, "book_detail.html", context)

            if len(offered_book) > 200:
                messages.error(request, "Offered book title must be at most 200 characters.")
                return render(request, "book_detail.html", context)

            if not book.is_available:
                messages.error(request, "This book is no longer available for trade.")
                return redirect("book_detail", book_id=book.id)

            TradeRequest.objects.create(
                book=book,
                requester=request.user,
                offered_book=offered_book,
                message=message,
            )
            messages.success(request, "Trade request sent!")
            return redirect("book_detail", book_id=book.id)

    return render(request, "book_detail.html", context)


@login_required
def respond_trade_view(request, trade_id, action):
    trade = get_object_or_404(
        TradeRequest.objects.select_related("book", "book__owner"),
        id=trade_id,
        book__owner=request.user,
        status=TradeRequest.Status.PENDING,
    )
    if action not in ("accept", "decline"):
        return redirect("book_detail", book_id=trade.book.id)

    if request.method == "POST":
        if action == "accept":
            trade.status = TradeRequest.Status.ACCEPTED
            trade.book.is_available = False
            trade.book.save(update_fields=["is_available", "updated_at"])
            messages.success(request, f"Trade accepted! Reach out to @{trade.requester.username} to arrange the swap.")
        else:
            trade.status = TradeRequest.Status.DECLINED
            messages.success(request, "Trade request declined.")
        trade.save(update_fields=["status", "updated_at"])

    return redirect("book_detail", book_id=trade.book.id)
