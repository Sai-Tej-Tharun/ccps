import io
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from pypdf import PdfReader
from rest_framework.test import APITestCase

from cards.models import Card

from .models import Transaction
from .statement import get_statement_data, render_statement_pdf

User = get_user_model()


class MonthlyStatementTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="a@example.com", email="a@example.com", password="StrongPass123", first_name="Ann", last_name="Lee"
        )
        self.other = User.objects.create_user(username="b@example.com", email="b@example.com", password="StrongPass123")
        self.card = Card.objects.create(
            user=self.user, brand="VISA", masked_number="**** **** **** 4242", last4="4242",
            cardholder_name="Ann Lee", expiry_month=12, expiry_year=2035,
        )
        other_card = Card.objects.create(
            user=self.other, brand="VISA", masked_number="**** **** **** 9999", last4="9999",
            cardholder_name="Bob", expiry_month=12, expiry_year=2035,
        )
        self.year, self.month = 2026, 3
        self._txn(self.user, self.card, "100.00", "t1", Transaction.Status.SUCCESS, datetime(2026, 3, 1, 0, 0, tzinfo=dt_timezone.utc))
        self._txn(self.user, self.card, "40.50", "t2", Transaction.Status.SUCCESS, datetime(2026, 3, 31, 23, 59, tzinfo=dt_timezone.utc))
        self._txn(self.user, self.card, "700.00", "t3", Transaction.Status.FAILED, datetime(2026, 3, 15, 12, 0, tzinfo=dt_timezone.utc))
        self._txn(self.user, self.card, "11.00", "t4", Transaction.Status.SUCCESS, datetime(2026, 4, 1, 0, 0, tzinfo=dt_timezone.utc))  # next month
        self._txn(self.user, self.card, "12.00", "t5", Transaction.Status.SUCCESS, datetime(2026, 2, 28, 23, 59, tzinfo=dt_timezone.utc))  # previous month
        self._txn(self.other, other_card, "999.00", "t6", Transaction.Status.SUCCESS, datetime(2026, 3, 10, 9, 0, tzinfo=dt_timezone.utc))

    @staticmethod
    def _txn(user, card, amount, ref, txn_status, when):
        txn = Transaction.objects.create(user=user, card=card, amount=Decimal(amount), status=txn_status, reference=ref)
        Transaction.objects.filter(pk=txn.pk).update(created_at=when)

    # ---- data -------------------------------------------------------------
    def test_data_is_scoped_to_user_and_month(self):
        data = get_statement_data(self.user, self.year, self.month)
        self.assertEqual([t.reference for t in data["transactions"]], ["t1", "t3", "t2"])
        self.assertEqual(data["spending_by_currency"], {"USD": Decimal("140.50")})  # successful only
        self.assertEqual(data["counts"], {"SUCCESS": 2, "FAILED": 1, "PENDING": 0})

    def test_pdf_contains_masked_card_and_totals_but_no_other_users_data(self):
        pdf = render_statement_pdf(get_statement_data(self.user, self.year, self.month))
        text = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)
        self.assertIn("**** **** **** 4242", text)
        self.assertIn("USD 140.50", text)
        self.assertIn("March 2026", text)
        self.assertNotIn("9999", text)
        self.assertNotIn("b@example.com", text)

    def test_empty_month_still_renders(self):
        pdf = render_statement_pdf(get_statement_data(self.user, 2025, 1))
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_many_transactions_span_pages(self):
        for i in range(120):
            self._txn(self.user, self.card, "1.00", f"bulk{i}", Transaction.Status.SUCCESS, datetime(2026, 3, 5, 10, i % 60, tzinfo=dt_timezone.utc))
        pdf = render_statement_pdf(get_statement_data(self.user, self.year, self.month))
        self.assertGreater(len(PdfReader(io.BytesIO(pdf)).pages), 1)

    # ---- endpoint -----------------------------------------------------------
    def test_requires_authentication(self):
        self.assertEqual(self.client.get("/api/transactions/statement/?year=2026&month=3").status_code, 401)

    def test_download_returns_pdf_attachment(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/transactions/statement/?year=2026&month=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn('filename="statement_2026_03.pdf"', response["Content-Disposition"])
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_defaults_to_current_month(self):
        self.client.force_authenticate(self.user)
        now = timezone.now()
        response = self.client.get("/api/transactions/statement/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"statement_{now.year}_{now.month:02d}.pdf", response["Content-Disposition"])

    def test_rejects_invalid_periods(self):
        self.client.force_authenticate(self.user)
        for query in ["year=2026&month=13", "year=2026&month=0", "year=abc&month=1", "year=1999&month=1",
                      "year=2026", "month=3", "year=2999&month=1"]:
            self.assertEqual(self.client.get(f"/api/transactions/statement/?{query}").status_code, 400, msg=query)