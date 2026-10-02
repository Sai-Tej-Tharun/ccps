from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from transactions.models import Transaction

User = get_user_model()


class DailySummaryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a@example.com", email="a@example.com", password="StrongPass123")
        self.admin = User.objects.create_superuser(username="admin@example.com", email="admin@example.com", password="StrongPass123")
        Transaction.objects.create(user=self.user, amount=Decimal("100.00"), status="SUCCESS", reference="ref-1")
        Transaction.objects.create(user=self.user, amount=Decimal("50.00"), status="FAILED", reference="ref-2")

        self.user_token = self._login("a@example.com")
        self.admin_token = self._login("admin@example.com")

    def _login(self, email):
        response = self.client.post("/api/auth/login/", {"email": email, "password": "StrongPass123"}, format="json")
        return response.data["access"]

    def test_regular_user_forbidden(self):
        response = self.client.get("/api/adminpanel/daily-summary/", HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_gets_aggregated_summary(self):
        response = self.client.get("/api/adminpanel/daily-summary/", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # both transactions created today
        today_row = response.data[0]
        self.assertEqual(today_row["total_count"], 2)
        self.assertEqual(today_row["success_count"], 1)
        self.assertEqual(today_row["failed_count"], 1)
        self.assertEqual(today_row["total_success_amount"], "100.00")
