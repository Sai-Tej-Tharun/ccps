from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Transaction

User = get_user_model()


class TransactionListTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a@example.com", email="a@example.com", password="StrongPass123")
        self.other = User.objects.create_user(username="b@example.com", email="b@example.com", password="StrongPass123")
        self.admin = User.objects.create_superuser(username="admin@example.com", email="admin@example.com", password="StrongPass123")

        Transaction.objects.create(user=self.user, amount=Decimal("50.00"), status="SUCCESS", reference="ref-1")
        Transaction.objects.create(user=self.user, amount=Decimal("10.00"), status="FAILED", reference="ref-2")
        Transaction.objects.create(user=self.other, amount=Decimal("99.00"), status="SUCCESS", reference="ref-3")

        self.user_token = self._login("a@example.com")
        self.admin_token = self._login("admin@example.com")

    def _login(self, email):
        response = self.client.post("/api/auth/login/", {"email": email, "password": "StrongPass123"}, format="json")
        return response.data["access"]

    def test_requires_authentication(self):
        response = self.client.get("/api/transactions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_sees_only_own_transactions(self):
        response = self.client.get("/api/transactions/", HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)
        for row in results:
            self.assertEqual(row["user_email"], "a@example.com")

    def test_admin_sees_all_transactions(self):
        response = self.client.get("/api/transactions/", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 3)

    def test_filter_by_status(self):
        response = self.client.get(
            "/api/transactions/?status=FAILED", HTTP_AUTHORIZATION=f"Bearer {self.user_token}"
        )
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["reference"], "ref-2")

    def test_filter_by_amount_range(self):
        response = self.client.get(
            "/api/transactions/?min_amount=20&max_amount=100", HTTP_AUTHORIZATION=f"Bearer {self.user_token}"
        )
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["reference"], "ref-1")

    def test_csv_export_requires_admin(self):
        response = self.client.get("/api/transactions/export/", HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_csv_export_as_admin_succeeds(self):
        response = self.client.get("/api/transactions/export/", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        body = response.content.decode()
        self.assertIn("ref-1", body)
        self.assertIn("ref-3", body)
