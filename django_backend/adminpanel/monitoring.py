"""
Request monitoring for the Django API: response time + failures, stored in
adminpanel_requestlog and logged through the "ccps.requests" logger.
The FastAPI service writes to the same table (fastapi_backend/monitoring.py).
"""

import logging
import os
import random
import time
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("ccps.requests")

SLOW_REQUEST_MS = int(os.environ.get("SLOW_REQUEST_MS", "1000"))
RETENTION_DAYS = int(os.environ.get("REQUEST_LOG_RETENTION_DAYS", "14"))


class RequestMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        response["X-Response-Time-ms"] = str(elapsed_ms)
        self._record(request, response.status_code, elapsed_ms)
        return response

    def process_exception(self, request, exception):
        # Remember the failure so the request row says what went wrong; Django still returns its 500.
        request._metrics_error = f"{type(exception).__name__}: {exception}"[:255]
        logger.error("Unhandled error on %s %s", request.method, request.path, exc_info=exception)
        return None

    def _record(self, request, status_code, elapsed_ms):
        if not request.path.startswith("/api/") or not getattr(settings, "REQUEST_METRICS_ENABLED", True):
            return

        match = getattr(request, "resolver_match", None)
        route = "/" + match.route.lstrip("/") if match and match.route else request.path
        level = logging.ERROR if status_code >= 500 else logging.WARNING if elapsed_ms >= SLOW_REQUEST_MS else logging.INFO
        logger.log(level, "%s %s -> %s in %sms", request.method, route, status_code, elapsed_ms)

        from .models import RequestLog  # imported lazily: models are not ready when settings load

        try:
            RequestLog.objects.create(
                service="django",
                method=request.method[:8],
                path=route[:200],
                status_code=status_code,
                duration_ms=elapsed_ms,
                error=getattr(request, "_metrics_error", ""),
                created_at=timezone.now(),
            )
            if random.random() < 0.002:  # now and then, drop rows older than the retention period
                RequestLog.objects.filter(created_at__lt=timezone.now() - timedelta(days=RETENTION_DAYS)).delete()
        except Exception:  # noqa: BLE001 - monitoring must never break a request
            logger.warning("Could not store request metrics", exc_info=True)