import csv

from django.conf import settings
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from accounts.permissions import require
from accounts.rbac import Perm, has_permission
from adminpanel.audit import log_admin_action

from .filters import TransactionFilter
from .models import Transaction
from .serializers import StatementQuerySerializer, TransactionSerializer
from .statement import get_statement_data, render_statement_pdf


class TransactionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"  # ?page_size=50
    max_page_size = 100  # a client can never ask for the whole table in one go


class TransactionListView(ListAPIView):
    """
    GET /api/transactions/
    Customers see only their own transactions. A staff role that holds
    transactions.view_all (Admin, Support, Read-Only) sees everyone's.

    Filters : status, date_from, date_to, min_amount, max_amount, category,
              fraud_status, card (masked number, e.g. "**** 4242")
    Sorting : ?ordering=-created_at (default) | created_at | amount | -amount | status
    Paging  : ?page=2&page_size=20 (max 100)
    """

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TransactionFilter
    pagination_class = TransactionPagination
    ordering_fields = ["created_at", "amount", "status", "id"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        user = self.request.user
        qs = Transaction.objects.select_related("user", "card").only(
            "id", "reference", "amount", "currency", "status", "failure_reason", "category",
            "fraud_status", "created_at", "updated_at", "user__email", "card__last4", "card__brand",
        )
        return qs if has_permission(user, Perm.TRANSACTIONS_VIEW_ALL) else qs.filter(user=user)


class TransactionExportCSVView(APIView):
    """
    GET /api/transactions/export/  — admin-only. Same filters as the list
    endpoint, streamed back as a CSV download instead of JSON.
    """

    permission_classes = [require(Perm.TRANSACTIONS_EXPORT)]

    def get(self, request):
        queryset = Transaction.objects.select_related("user", "card").all()
        queryset = TransactionFilter(request.GET, queryset=queryset).qs

        row_count = queryset.count()
        log_admin_action(
            request,
            "Exported transactions CSV",
            target_type="transactions",
            changes={"filters": dict(request.GET), "row_count": row_count},
            details=f"filters={dict(request.GET)}, row_count={row_count}",
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions_export.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ["id", "reference", "user_email", "card_brand", "card_last4", "amount", "currency", "status", "created_at"]
        )
        for txn in queryset.iterator(chunk_size=2000):  # streams rows instead of loading the whole table
            writer.writerow(
                [
                    txn.id,
                    txn.reference,
                    txn.user.email,
                    txn.card.brand if txn.card else "",
                    txn.card.last4 if txn.card else "",
                    txn.amount,
                    txn.currency,
                    txn.status,
                    txn.created_at.isoformat(),
                ]
            )
        return response
class StatementRateThrottle(UserRateThrottle):
    scope = "statement"  # rate set in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]


class MonthlyStatementView(APIView):
    """
    GET /api/transactions/statement/?year=2026&month=9  - downloadable PDF statement.

    Always the *requesting user's own* data (the user is never taken from the
    request), so one customer can never download another's statement.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [] if settings.TESTING else [StatementRateThrottle]

    def get(self, request):
        query = StatementQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        year, month = query.validated_data["year"], query.validated_data["month"]

        pdf = render_statement_pdf(get_statement_data(request.user, year, month))

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="statement_{year}_{month:02d}.pdf"'
        response["Cache-Control"] = "no-store"  # financial data - don't let proxies/browsers cache it
        return response