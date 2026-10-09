"""
Admin card management - every view here is staff-only (IsAdminUser) and every
state change is written to the AdminActionLog audit trail.

GET   /api/adminpanel/cards/                      all cards (?search=, ?status=active|blocked)
POST  /api/adminpanel/cards/<id>/block/           block a card (e-mails the owner)
POST  /api/adminpanel/cards/<id>/unblock/         unblock a card
PATCH /api/adminpanel/cards/<id>/credit-limit/    body: {"credit_limit": "7500.00"}
GET   /api/adminpanel/cards/<id>/activity/        that card's transactions, newest first
"""

from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import Count, DecimalField, Max, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import require
from accounts.rbac import Perm
from cards.emails import send_card_blocked_email
from cards.models import Card
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer

from .card_serializers import AdminCardSerializer, CreditLimitUpdateSerializer
from .audit import log_admin_action


def annotated_cards():
    spent = Sum("transactions__amount", filter=Q(transactions__status=Transaction.Status.SUCCESS))
    return (
        Card.objects.select_related("user")
        .annotate(
            transaction_count=Count("transactions"),
            total_spent=Coalesce(
                spent, Value(Decimal("0.00")), output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            last_activity=Max("transactions__created_at"),
        )
        .order_by("-created_at", "-id")
    )


def _serialize(card_id):
    return AdminCardSerializer(annotated_cards().get(pk=card_id)).data


class AdminCardListView(ListAPIView):
    permission_classes = [require(Perm.CARDS_VIEW)]
    serializer_class = AdminCardSerializer

    def get_queryset(self):
        params = self.request.query_params
        queryset = annotated_cards()

        status_filter = params.get("status", "").strip().lower()
        if status_filter == "blocked":
            queryset = queryset.filter(is_blocked=True)
        elif status_filter == "active":
            queryset = queryset.filter(is_blocked=False)
        elif status_filter:
            raise ValidationError({"status": "Must be 'active' or 'blocked'."})

        search = params.get("search", "").strip()[:100]
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search)
                | Q(cardholder_name__icontains=search)
                | Q(last4=search)
            )
        return queryset


class _BlockStateView(APIView):
    """Shared implementation of block / unblock."""

    permission_classes = [require(Perm.CARDS_BLOCK)]  # Admin and Support
    block = True

    def post(self, request, pk):
        with db_transaction.atomic():
            # Row lock: two admins acting on the same card at once can't both "win".
            card = get_object_or_404(Card.objects.select_for_update(), pk=pk)
            if card.is_blocked == self.block:
                state = "already blocked" if self.block else "not blocked"
                return Response({"detail": f"This card is {state}."}, status=status.HTTP_409_CONFLICT)

            card.is_blocked = self.block
            card.blocked_at = timezone.now() if self.block else None
            card.save(update_fields=["is_blocked", "blocked_at"])

            log_admin_action(
                request,
                "Blocked card" if self.block else "Unblocked card",
                target_type="card",
                target_id=card.pk,
                changes={"is_blocked": {"old": not self.block, "new": self.block}},
                details=f"card_id={card.pk}, owner_id={card.user_id}, last4={card.last4}",
            )
            if self.block:
                # Only e-mail once the change is really committed.
                db_transaction.on_commit(lambda: send_card_blocked_email(card))

        return Response(_serialize(card.pk))


class AdminCardBlockView(_BlockStateView):
    block = True


class AdminCardUnblockView(_BlockStateView):
    block = False


class AdminCardCreditLimitView(APIView):
    permission_classes = [require(Perm.CARDS_UPDATE_LIMIT)]  # Admin only

    def patch(self, request, pk):
        serializer = CreditLimitUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_limit = serializer.validated_data["credit_limit"]

        with db_transaction.atomic():
            card = get_object_or_404(Card.objects.select_for_update(), pk=pk)
            old_limit = card.credit_limit
            if old_limit != new_limit:
                card.credit_limit = new_limit
                card.save(update_fields=["credit_limit"])
                log_admin_action(
                    request,
                    "Updated card credit limit",
                    target_type="card",
                    target_id=card.pk,
                    changes={"credit_limit": {"old": str(old_limit), "new": str(new_limit)}},
                    details=f"card_id={card.pk}, owner_id={card.user_id}, last4={card.last4}, old={old_limit}, new={new_limit}",
                )

        return Response(_serialize(card.pk))


class AdminCardActivityView(ListAPIView):
    permission_classes = [require(Perm.CARDS_VIEW)]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        card = get_object_or_404(Card, pk=self.kwargs["pk"])
        return Transaction.objects.filter(card=card).select_related("user", "card").order_by("-created_at", "-id")