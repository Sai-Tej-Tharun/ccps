import csv

from django.http import HttpResponse
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from adminpanel.models import AdminActionLog

from .filters import TransactionFilter
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionListView(ListAPIView):
    """
    GET /api/transactions/
    Regular users see only their own transaction history. Staff/admin
    users (is_staff=True) see everyone's — this same endpoint backs both
    the user's "Transaction History" page and the admin dashboard's
    "View Transactions" list, filtered identically either way.

    Query params: status, date_from, date_to, min_amount, max_amount
    """

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TransactionFilter

    def get_queryset(self):
        user = self.request.user
        qs = Transaction.objects.select_related("user", "card")
        return qs if user.is_staff else qs.filter(user=user)


class TransactionExportCSVView(APIView):
    """
    GET /api/transactions/export/  — admin-only. Same filters as the list
    endpoint, streamed back as a CSV download instead of JSON.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        queryset = Transaction.objects.select_related("user", "card").all()
        queryset = TransactionFilter(request.GET, queryset=queryset).qs

        AdminActionLog.objects.create(
            admin_user=request.user,
            action="Exported transactions CSV",
            details=f"filters={dict(request.GET)}, row_count={queryset.count()}",
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions_export.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ["id", "reference", "user_email", "card_brand", "card_last4", "amount", "currency", "status", "created_at"]
        )
        for txn in queryset:
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
