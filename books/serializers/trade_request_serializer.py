from rest_framework import serializers

from books.models.trade_request import TradeRequest


class TradeRequestSerializer(serializers.ModelSerializer):
    requester_username = serializers.CharField(source="requester.username", read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True)
    book_owner_username = serializers.CharField(source="book.owner.username", read_only=True)

    class Meta:
        model = TradeRequest
        fields = [
            "id",
            "book",
            "book_title",
            "book_owner_username",
            "requester_username",
            "offered_book",
            "message",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        book = attrs["book"]

        if book.owner == request.user:
            raise serializers.ValidationError("You cannot request a trade for your own book.")

        if not book.is_available:
            raise serializers.ValidationError("This book is no longer available for trade.")

        already_pending = TradeRequest.objects.filter(
            book=book, requester=request.user, status=TradeRequest.Status.PENDING
        ).exists()
        if already_pending:
            raise serializers.ValidationError("You already have a pending trade request for this book.")

        return attrs
