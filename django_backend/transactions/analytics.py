"""
Card usage analytics + export.

GET /api/transactions/analytics/monthly/      ?months=6&currency=USD&scope=own|all
GET /api/transactions/analytics/categories/   same filters
GET /api/transactions/analytics/utilization/  same filters (currency is ignored; limits have no currency)

scope=own (default) = the caller's own transactions.
scope=all           = everybody's; needs the analytics.view permission (Admin / Support / Read-Only).
Only SUCCESS transactions count as spending.
"""

from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.rbac import Perm, has_permission
from cards.models import Card

from .models import Transaction

ZERO = Decimal("0.00")
MONEY = DecimalField(max_digits=14, decimal_places=2)


class AnalyticsQuerySerializer(serializers.Serializer):
    months = serializers.IntegerField(min_value=1, max_value=24, default=6)
    currency = serializers.RegexField(r"^[A-Za-z]{3}$", default="USD")
    scope = serializers.ChoiceField(choices=["own", "all"], default="own")
    type = serializers.ChoiceField(choices=["csv", "pdf"], default="csv")

    def validate_currency(self, value):
        return value.upper()


def _params(request):
    serializer = AnalyticsQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    params = serializer.validated_data
    if params["scope"] == "all" and not has_permission(request.user, Perm.ANALYTICS_VIEW):
        raise PermissionDenied("Your role cannot view analytics for all customers.")
    return params


def _scoped(request, params):
    qs = Transaction.objects.all()
    return qs if params["scope"] == "all" else qs.filter(user=request.user)


def _month_start(today, months_back):
    index = today.year * 12 + (today.month - 1) - months_back
    return date(index // 12, index % 12 + 1, 1)


def _money(value):
    return f"{Decimal(value or 0).quantize(Decimal('0.01')):.2f}"


def monthly_summary(request, params):
    today = timezone.localdate()
    first = _month_start(today, params["months"] - 1)
    rows = (
        _scoped(request, params)
        .filter(currency=params["currency"], created_at__date__gte=first)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            total_spent=Coalesce(Sum("amount", filter=Q(status="SUCCESS")), Value(ZERO), output_field=MONEY),
            success_count=Count("id", filter=Q(status="SUCCESS")),
            failed_count=Count("id", filter=Q(status="FAILED")),
        )
    )
    by_month = {(r["month"].year, r["month"].month): r for r in rows}

    result = []
    for back in range(params["months"] - 1, -1, -1):  # oldest -> newest, empty months included
        start = _month_start(today, back)
        row = by_month.get((start.year, start.month))
        result.append(
            {
                "month": start.strftime("%Y-%m"),
                "label": start.strftime("%b %Y"),
                "total_spent": _money(row["total_spent"] if row else 0),
                "success_count": row["success_count"] if row else 0,
                "failed_count": row["failed_count"] if row else 0,
            }
        )
    return result


def category_breakdown(request, params):
    first = _month_start(timezone.localdate(), params["months"] - 1)
    rows = list(
        _scoped(request, params)
        .filter(currency=params["currency"], status="SUCCESS", created_at__date__gte=first)
        .values("category")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
    grand_total = sum((r["total"] for r in rows), ZERO)
    labels = dict(Transaction.Category.choices)
    return [
        {
            "category": r["category"],
            "label": labels.get(r["category"], r["category"].title()),
            "total": _money(r["total"]),
            "count": r["count"],
            "percent": round(float(r["total"] * 100 / grand_total), 1) if grand_total else 0,
        }
        for r in rows
    ]


def utilization(request, params):
    """Credit utilization = this month's successful spend / total credit limit (same maths as the dashboard)."""
    month_start = _month_start(timezone.localdate(), 0)
    spent_filter = Q(transactions__status="SUCCESS", transactions__created_at__date__gte=month_start)
    cards = Card.objects.all() if params["scope"] == "all" else Card.objects.filter(user=request.user)
    cards = cards.annotate(spent=Coalesce(Sum("transactions__amount", filter=spent_filter), Value(ZERO), output_field=MONEY))

    total_limit = ZERO
    total_spent = ZERO
    per_card = []
    for card in cards.select_related("user"):
        total_limit += card.credit_limit
        total_spent += card.spent
        per_card.append(
            {
                "card_id": card.id,
                "label": f"{card.brand} {card.masked_number[-4:]}",
                "credit_limit": _money(card.credit_limit),
                "spent": _money(card.spent),
                "utilization_percent": round(min(float(card.spent * 100 / card.credit_limit), 100.0), 1) if card.credit_limit else 0,
                "is_blocked": card.is_blocked,
            }
        )
    per_card.sort(key=lambda c: c["utilization_percent"], reverse=True)
    return {
        "total_limit": _money(total_limit),
        "total_spent": _money(total_spent),
        "available": _money(max(total_limit - total_spent, ZERO)),
        "utilization_percent": round(min(float(total_spent * 100 / total_limit), 100.0), 1) if total_limit else 0,
        "cards": per_card[:10],
        "card_count": len(per_card),
    }


class MonthlySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(monthly_summary(request, _params(request)))


class CategoryBreakdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(category_breakdown(request, _params(request)))


class UtilizationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(utilization(request, _params(request)))