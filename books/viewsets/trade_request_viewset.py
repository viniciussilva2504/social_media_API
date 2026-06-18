from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.models.trade_request import TradeRequest
from books.serializers.trade_request_serializer import TradeRequestSerializer


class TradeRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TradeRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Returns requests sent by the user OR on books owned by the user
        return (
            TradeRequest.objects.filter(
                requester=user
            ) | TradeRequest.objects.filter(
                book__owner=user
            )
        ).select_related(
            "book", "book__owner", "requester"
        ).distinct().order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        trade = self.get_object()
        if trade.book.owner != request.user:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        if trade.status != TradeRequest.Status.PENDING:
            return Response({"detail": "This request is no longer pending."}, status=status.HTTP_400_BAD_REQUEST)
        trade.status = TradeRequest.Status.ACCEPTED
        trade.save(update_fields=["status", "updated_at"])
        return Response(TradeRequestSerializer(trade).data)

    @action(detail=True, methods=["post"], url_path="decline")
    def decline(self, request, pk=None):
        trade = self.get_object()
        if trade.book.owner != request.user:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        if trade.status != TradeRequest.Status.PENDING:
            return Response({"detail": "This request is no longer pending."}, status=status.HTTP_400_BAD_REQUEST)
        trade.status = TradeRequest.Status.DECLINED
        trade.save(update_fields=["status", "updated_at"])
        return Response(TradeRequestSerializer(trade).data)
