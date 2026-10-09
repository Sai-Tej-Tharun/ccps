from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import require
from accounts.rbac import Perm
from transactions.models import Transaction

from .models import AdminActionLog
from .serializers import AdminActionLogSerializer


class DailySummaryView(APIView):
    """
    GET /api/adminpanel/daily-summary/?days=30   (admin-only)

    Returns one row per calendar day (most recent first) with the number
    of transactions, total successful amount, and counts by status — the
    data behind the admin dashboard's "Daily Payment Summary".
    """

    permission_classes = [require(Perm.ANALYTICS_VIEW)]

    def get(self, request):
        try:
            days = max(1, min(int(request.GET.get("days", 30)), 365))
        except ValueError:
            days = 30

        since = timezone.now() - timedelta(days=days)

        rows = (
            Transaction.objects.filter(created_at__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                total_count=Count("id"),
                success_count=Count("id", filter=Q(status=Transaction.Status.SUCCESS)),
                failed_count=Count("id", filter=Q(status=Transaction.Status.FAILED)),
                pending_count=Count("id", filter=Q(status=Transaction.Status.PENDING)),
                total_success_amount=Sum("amount", filter=Q(status=Transaction.Status.SUCCESS)),
            )
            .order_by("-day")
        )

        data = [
            {
                "date": row["day"].isoformat(),
                "total_count": row["total_count"],
                "success_count": row["success_count"],
                "failed_count": row["failed_count"],
                "pending_count": row["pending_count"],
                # Explicit 2dp formatting rather than str() on the raw
                # aggregate — SQLite's decimal emulation and MySQL's native
                # DECIMAL don't stringify identically, and the frontend
                # always wants a plain "100.00"-style amount either way.
                "total_success_amount": f"{float(row['total_success_amount'] or 0):.2f}",
            }
            for row in rows
        ]
        return Response(data)


class AdminActionLogListView(ListAPIView):
    """GET /api/adminpanel/logs/  (admin-only) — audit trail of admin actions."""

    permission_classes = [require(Perm.AUDIT_VIEW)]  # Admin only
    serializer_class = AdminActionLogSerializer

    def get_queryset(self):
        qs = AdminActionLog.objects.select_related("admin_user")
        params = self.request.query_params
        if params.get("action"):
            qs = qs.filter(action__icontains=params["action"][:100])
        if params.get("target_type"):
            qs = qs.filter(target_type=params["target_type"][:40])
        if params.get("admin"):
            qs = qs.filter(admin_user__email__icontains=params["admin"][:100])
        return qs
