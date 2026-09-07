from django.urls import path
from books.views import (
    biblioteca_view,
    add_book_view,
    delete_book_view,
    toggle_book_availability_view,
    book_detail_view,
    respond_trade_view,
    import_book_preview_view,
)

urlpatterns = [
    path("book-import-preview/", import_book_preview_view, name="import_book_preview"),
    path("biblioteca/<str:username>/", biblioteca_view, name="biblioteca"),
    path("biblioteca/<str:username>/add/", add_book_view, name="add_book"),
    path("book/<int:book_id>/", book_detail_view, name="book_detail"),
    path("book/<int:book_id>/delete/", delete_book_view, name="delete_book"),
    path("book/<int:book_id>/toggle-availability/", toggle_book_availability_view, name="toggle_book_availability"),
    path("trade/<int:trade_id>/<str:action>/", respond_trade_view, name="respond_trade"),
]
