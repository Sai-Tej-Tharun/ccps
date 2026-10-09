"""GET /api/adminpanel/system-health/?hours=24 - basic health numbers for the admin dashboard."""

import time
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.db.models import Avg, Count, Max, Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import require
from accounts.rbac import Perm
from cards.models import Card

from .models import FraudLog, RequestLog


def _check_database():
    started = time.perf_counter()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {"status": "ok", "latency_ms": int((time.perf_counter() - started) * 1000)}
    except Exception:  # noqa: BLE001
        return {"status": "down", "latency_ms": None}


def _check_fastapi():
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(settings.FASTAPI_HEALTH_URL, timeout=2) as reply:  # noqa: S310 - fixed URL from settings
            ok = reply.status == 200
        return {"status": "ok" if ok else "down", "latency_ms": int((time.perf_counter() - started) * 1000)}
    except Exception:  # noqa: BLE001
        return {"status": "down", "latency_ms": None}


def _round(value):
    return None if value is None else round(float(value), 1)


class SystemHealthView(APIView):
    permission_classes = [require(Perm.MONITORING_VIEW)]

    def get(self, request):
        try:
            hours = max(1, min(int(request.query_params.get("hours", 24)), 168))
        except ValueError:
            hours = 24
        since = timezone.now() - timedelta(hours=hours)
        logs = RequestLog.objects.filter(created_at__gte=since)

        totals = logs.aggregate(
            total=Count("id"),
            avg_ms=Avg("duration_ms"),
            server_errors=Count("id", filter=Q(status_code__gte=500)),
            client_errors=Count("id", filter=Q(status_code__gte=400, status_code__lt=500)),
        )
        total = totals["total"]
        p95 = None
        if total:
            p95 = logs.order_by("duration_ms").values_list("duration_ms", flat=True)[min(total - 1, int(total * 0.95))]

        by_service = [
            {"service": r["service"], "requests": r["total"], "avg_ms": _round(r["avg_ms"]), "errors": r["errors"]}
            for r in logs.values("service")
            .annotate(total=Count("id"), avg_ms=Avg("duration_ms"), errors=Count("id", filter=Q(status_code__gte=500)))
            .order_by("service")
        ]
        slowest = [
            {**r, "avg_ms": _round(r["avg_ms"])}
            for r in logs.values("service", "method", "path")
            .annotate(requests=Count("id"), avg_ms=Avg("duration_ms"), max_ms=Max("duration_ms"))
            .order_by("-avg_ms")[:5]
        ]
        recent_errors = list(
            logs.filter(status_code__gte=500).values("service", "method", "path", "status_code", "error", "created_at")[:10]
        )

        return Response(
            {
                "checked_at": timezone.now(),
                "window_hours": hours,
                "services": {"database": _check_database(), "payment_service": _check_fastapi()},
                "requests": {
                    "total": total,
                    "avg_ms": _round(totals["avg_ms"]),
                    "p95_ms": p95,
                    "server_errors": totals["server_errors"],
                    "client_errors": totals["client_errors"],
                    "error_rate_percent": round(totals["server_errors"] * 100 / total, 2) if total else 0,
                },
                "by_service": by_service,
                "slowest_endpoints": slowest,
                "recent_errors": recent_errors,
                "open_fraud_alerts": FraudLog.objects.filter(reviewed=False).count(),
                "blocked_cards": Card.objects.filter(is_blocked=True).count(),
            }
        )