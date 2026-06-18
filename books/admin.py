from django.contrib import admin
from books.models.book import Book
from books.models.trade_request import TradeRequest


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "book_author", "owner", "is_available", "created_at"]
    list_filter = ["is_available"]
    search_fields = ["title", "book_author", "owner__username"]


@admin.register(TradeRequest)
class TradeRequestAdmin(admin.ModelAdmin):
    list_display = ["book", "requester", "offered_book", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["book__title", "requester__username", "offered_book"]
