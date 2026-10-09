from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import UserRole
from adminpanel.models import AdminActionLog
from cards.models import Card

from .models import Transaction

User = get_user_model()


def make_user(email, role=None):
    user = User.objects.create_user(username=email, email=email, password="StrongPass123")
    if role:
        UserRole.objects.create(user=user, role=role)
    return user


def make_card(user, last4, limit="1000.00"):
    return Card.objects.create(
        user=user, brand="VISA", masked_number=f"**** **** **** {last4}", last4=last4,
        cardholder_name="Test", expiry_month=12, expiry_year=2035, credit_limit=Decimal(limit),
    )


def make_txn(user, card, amount, status="SUCCESS", category="OTHER", days_ago=0, ref=None):
    txn = Transaction.objects.create(
        user=user, card=card, amount=Decimal(amount), status=status, category=category,
        reference=ref or f"ref-{Transaction.objects.count() + 1}",
    )
    Transaction.objects.filter(pk=txn.pk).update(created_at=timezone.now() - timedelta(days=days_ago))
    return txn


class AnalyticsTests(APITestCase):
    def setUp(self):
        self.user = make_user("u@example.com")
        self.other = make_user("o@example.com")
        self.card = make_card(self.user, "4242", "1000.00")
        other_card = make_card(self.other, "1111", "2000.00")
        make_txn(self.user, self.card, "100.00", category="FOOD")
        make_txn(self.user, self.card, "150.00", category="TRAVEL")
        make_txn(self.user, self.card, "999.00", status="FAILED", category="TRAVEL")  # failed: not spending
        make_txn(self.user, self.card, "40.00", category="FOOD", days_ago=40)
        make_txn(self.other, other_card, "500.00", category="SHOPPING")
        self.client.force_authenticate(self.user)

    def test_monthly_summary_has_one_row_per_month_including_empty_ones(self):
        data = self.client.get("/api/transactions/analytics/monthly/?months=3").data
        self.assertEqual(len(data), 3)
        self.assertEqual(data[-1]["total_spent"], "250.00")
        self.assertEqual(data[-1]["failed_count"], 1)
        self.assertEqual(sum(Decimal(m["total_spent"]) for m in data), Decimal("290.00"))

    def test_category_breakdown_counts_only_successful_payments(self):
        data = {row["category"]: row for row in self.client.get("/api/transactions/analytics/categories/?months=3").data}
        self.assertEqual(data["FOOD"]["total"], "140.00")
        self.assertEqual(data["TRAVEL"]["total"], "150.00")
        self.assertEqual(data["FOOD"]["label"], "Food & dining")
        self.assertAlmostEqual(sum(r["percent"] for r in data.values()), 100, delta=0.2)

    def test_credit_utilization_uses_this_months_spend_over_the_limit(self):
        data = self.client.get("/api/transactions/analytics/utilization/").data
        self.assertEqual(data["total_limit"], "1000.00")
        self.assertEqual(data["total_spent"], "250.00")
        self.assertEqual(data["available"], "750.00")
        self.assertEqual(data["utilization_percent"], 25.0)
        self.assertEqual(data["cards"][0]["label"], "VISA 4242")

    def test_scope_all_needs_a_staff_role(self):
        self.assertEqual(self.client.get("/api/transactions/analytics/monthly/?scope=all").status_code, 403)
        self.client.force_authenticate(make_user("ro@example.com", "READ_ONLY"))
        data = self.client.get("/api/transactions/analytics/utilization/?scope=all").data
        self.assertEqual(data["total_limit"], "3000.00")
        self.assertEqual(data["total_spent"], "750.00")

    def test_query_validation(self):
        for query in ("months=0", "months=25", "months=abc", "currency=US", "scope=everyone"):
            self.assertEqual(self.client.get(f"/api/transactions/analytics/monthly/?{query}").status_code, 400, query)

    def test_export_csv_and_pdf(self):
        csv_response = self.client.get("/api/transactions/analytics/export/?type=csv&months=3")
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("text/csv", csv_response["Content-Type"])
        body = csv_response.content.decode()
        self.assertIn("Monthly spending", body)
        self.assertIn("Food & dining,140.00", body)
        pdf_response = self.client.get("/api/transactions/analytics/export/?type=pdf")
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))
        self.assertEqual(self.client.get("/api/transactions/analytics/export/?type=xml").status_code, 400)

    def test_all_customer_export_is_audit_logged(self):
        self.client.force_authenticate(make_user("ro@example.com", "READ_ONLY"))
        self.assertEqual(self.client.get("/api/transactions/analytics/export/?scope=all").status_code, 200)
        self.assertTrue(AdminActionLog.objects.filter(action="Exported analytics summary").exists())

    def test_login_is_required(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/transactions/analytics/monthly/").status_code, 401)


class TransactionSearchTests(APITestCase):
    def setUp(self):
        self.user = make_user("u@example.com")
        self.visa = make_card(self.user, "4242")
        self.second = make_card(self.user, "1111")
        make_txn(self.user, self.visa, "10.00", days_ago=30, ref="a")
        make_txn(self.user, self.visa, "250.00", status="FAILED", days_ago=10, ref="b")
        make_txn(self.user, self.second, "75.50", days_ago=2, ref="c")
        make_txn(self.user, self.second, "900.00", category="TRAVEL", days_ago=0, ref="d")
        self.client.force_authenticate(self.user)

    def refs(self, query):
        data = self.client.get(f"/api/transactions/?{query}").data
        return [row["reference"] for row in data["results"]]

    def test_date_range(self):
        start = (timezone.now() - timedelta(days=12)).date().isoformat()
        end = (timezone.now() - timedelta(days=1)).date().isoformat()
        self.assertEqual(sorted(self.refs(f"date_from={start}&date_to={end}")), ["b", "c"])

    def test_amount_range(self):
        self.assertEqual(sorted(self.refs("min_amount=50&max_amount=300")), ["b", "c"])

    def test_status_and_category_filters(self):
        self.assertEqual(self.refs("status=FAILED"), ["b"])
        self.assertEqual(self.refs("category=TRAVEL"), ["d"])

    def test_masked_card_number_search(self):
        self.assertEqual(sorted(self.refs("card=4242")), ["a", "b"])
        self.assertEqual(sorted(self.refs("card=****%204242")), ["a", "b"])
        self.assertEqual(sorted(self.refs("card=**** **** **** 1111")), ["c", "d"])
        self.assertEqual(self.refs("card=%2A%2A%2A"), [])  # no digits -> nothing, never everything

    def test_sorting(self):
        self.assertEqual(self.refs("ordering=amount"), ["a", "c", "b", "d"])
        self.assertEqual(self.refs("ordering=-amount"), ["d", "b", "c", "a"])
        self.assertEqual(self.refs(""), ["d", "c", "b", "a"])  # newest first by default

    def test_server_side_pagination(self):
        page = self.client.get("/api/transactions/?page_size=2&ordering=amount").data
        self.assertEqual((page["count"], len(page["results"])), (4, 2))
        self.assertIsNotNone(page["next"])
        second = self.client.get("/api/transactions/?page_size=2&ordering=amount&page=2").data
        self.assertEqual([r["reference"] for r in second["results"]], ["b", "d"])

    def test_page_size_is_capped(self):
        for n in range(105):
            make_txn(self.user, self.visa, "1.00", ref=f"bulk-{n}")
        data = self.client.get("/api/transactions/?page_size=1000").data
        self.assertEqual(len(data["results"]), 100)

    def test_query_count_does_not_grow_with_the_number_of_rows(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as few:
            self.client.get("/api/transactions/")
        for n in range(40):
            make_txn(self.user, self.visa, "1.00", ref=f"many-{n}")
        with CaptureQueriesContext(connection) as many:
            self.client.get("/api/transactions/?page_size=100")
        self.assertEqual(len(few), len(many))  # no N+1: user and card come in the same query

    def test_fraud_status_hidden_from_customers_but_shown_to_staff(self):
        self.assertNotIn("fraud_status", self.client.get("/api/transactions/").data["results"][0])
        self.client.force_authenticate(make_user("s@example.com", "SUPPORT"))
        self.assertIn("fraud_status", self.client.get("/api/transactions/").data["results"][0])

    def test_invalid_values_are_rejected(self):
        self.assertEqual(self.client.get("/api/transactions/?status=NOPE").status_code, 400)
        self.assertEqual(self.client.get("/api/transactions/?min_amount=abc").status_code, 400)
        self.assertEqual(self.client.get("/api/transactions/?date_from=yesterday").status_code, 400)