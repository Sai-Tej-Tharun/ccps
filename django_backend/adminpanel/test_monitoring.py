from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import UserRole

from .models import RequestLog

User = get_user_model()


def make_user(email, role=None):
    user = User.objects.create_user(username=email, email=email, password="StrongPass123")
    if role:
        UserRole.objects.create(user=user, role=role)
    return user


class MonitoringTests(APITestCase):
    def test_middleware_logs_api_requests_with_route_pattern_and_timing(self):
        user = make_user("c@example.com")
        self.client.force_authenticate(user)
        response = self.client.get("/api/cards/")
        self.assertIn("X-Response-Time-ms", response)
        row = RequestLog.objects.get(path="/api/cards/")
        self.assertEqual((row.service, row.method, row.status_code), ("django", "GET", 200))
        self.assertGreaterEqual(row.duration_ms, 0)

    def test_client_errors_are_logged_and_non_api_paths_are_not(self):
        self.client.get("/api/cards/")  # 401: not logged in
        self.assertEqual(RequestLog.objects.get(path="/api/cards/").status_code, 401)
        self.client.get("/nowhere/")
        self.assertFalse(RequestLog.objects.filter(path="/nowhere/").exists())

    def test_unhandled_exception_is_recorded(self):
        self.client.raise_request_exception = False
        self.client.force_authenticate(make_user("c@example.com"))
        with mock.patch("cards.views.CardListCreateView.get_queryset", side_effect=RuntimeError("db exploded")):
            response = self.client.get("/api/cards/")
        self.assertEqual(response.status_code, 500)
        row = RequestLog.objects.get(status_code=500)
        self.assertIn("RuntimeError: db exploded", row.error)

    def test_system_health_summary(self):
        for ms, code in ((100, 200), (200, 200), (300, 500), (400, 404)):
            RequestLog.objects.create(service="django", method="GET", path="/api/x/", status_code=code, duration_ms=ms, error="boom" if code == 500 else "")
        RequestLog.objects.create(service="fastapi", method="POST", path="/payments/pay", status_code=201, duration_ms=50)
        RequestLog.objects.create(service="django", method="GET", path="/api/old/", status_code=200, duration_ms=9999,
                                  created_at=timezone.now() - timedelta(days=3))

        self.client.force_authenticate(make_user("c@example.com"))
        self.assertEqual(self.client.get("/api/adminpanel/system-health/").status_code, 403)

        self.client.force_authenticate(make_user("ro@example.com", "READ_ONLY"))
        with mock.patch("adminpanel.health_views._check_fastapi", return_value={"status": "ok", "latency_ms": 5}):
            data = self.client.get("/api/adminpanel/system-health/?hours=24").data
        self.assertEqual(data["services"]["database"]["status"], "ok")
        self.assertEqual(data["services"]["payment_service"]["status"], "ok")
        self.assertEqual(data["requests"]["server_errors"], 1)
        self.assertEqual(data["requests"]["client_errors"], 2)  # the 404 above + the 403 the customer just got
        self.assertEqual(data["requests"]["error_rate_percent"], round(100 / data["requests"]["total"], 2))
        self.assertEqual(data["recent_errors"][0]["error"], "boom")
        self.assertEqual(data["slowest_endpoints"][0]["path"], "/api/x/")
        self.assertEqual({s["service"] for s in data["by_service"]}, {"django", "fastapi"})
        self.assertNotIn(9999, [e["max_ms"] for e in data["slowest_endpoints"]])  # outside the 24h window

    def test_health_reports_a_down_payment_service(self):
        self.client.force_authenticate(make_user("ro@example.com", "READ_ONLY"))
        with mock.patch("adminpanel.health_views.urllib.request.urlopen", side_effect=OSError("refused")):
            data = self.client.get("/api/adminpanel/system-health/").data
        self.assertEqual(data["services"]["payment_service"], {"status": "down", "latency_ms": None})