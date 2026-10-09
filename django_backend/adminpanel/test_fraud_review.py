from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.models import UserRole
from cards.models import Card
from transactions.models import Transaction

from .models import AdminActionLog, FraudLog

User = get_user_model()


def make_user(email, role=None):
    user = User.objects.create_user(username=email, email=email, password="StrongPass123")
    if role:
        UserRole.objects.create(user=user, role=role)
    return user


class FraudReviewTests(APITestCase):
    def setUp(self):
        self.customer = make_user("c@example.com")
        self.support = make_user("support@example.com", "SUPPORT")
        self.read_only = make_user("ro@example.com", "READ_ONLY")
        card = Card.objects.create(
            user=self.customer, brand="VISA", masked_number="**** **** **** 4242", last4="4242",
            cardholder_name="C", expiry_month=12, expiry_year=2035,
        )
        self.txn = Transaction.objects.create(
            user=self.customer, card=card, amount="2500.00", status="SUCCESS", reference="fraud-1", fraud_status="FLAGGED"
        )
        self.log = FraudLog.objects.create(
            transaction=self.txn, user=self.customer, card=card, rule="HIGH_VALUE_BURST", severity="HIGH", details="3 payments"
        )
        FraudLog.objects.create(transaction=self.txn, user=self.customer, rule="MULTI_SOURCE", reviewed=True)

    def test_list_needs_fraud_view_and_supports_filters(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get("/api/adminpanel/fraud-logs/").status_code, 403)
        self.client.force_authenticate(self.read_only)
        self.assertEqual(self.client.get("/api/adminpanel/fraud-logs/").data["count"], 2)
        open_only = self.client.get("/api/adminpanel/fraud-logs/?reviewed=false").data
        self.assertEqual(open_only["count"], 1)
        self.assertEqual(open_only["results"][0]["reference"], "fraud-1")
        self.assertEqual(self.client.get("/api/adminpanel/fraud-logs/?rule=MULTI_SOURCE").data["count"], 1)
        self.assertEqual(self.client.get("/api/adminpanel/fraud-logs/?reviewed=maybe").status_code, 400)
        self.assertEqual(self.client.get("/api/adminpanel/fraud-logs/?rule=NOPE").status_code, 400)

    def test_review_updates_log_and_transaction_and_is_audited(self):
        self.client.force_authenticate(self.support)
        response = self.client.post(
            f"/api/adminpanel/fraud-logs/{self.log.pk}/review/",
            {"resolution": "CONFIRMED_FRAUD", "note": "  customer\nconfirmed "}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["resolution"], "CONFIRMED_FRAUD")
        self.assertEqual(response.data["review_note"], "customer confirmed")
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.fraud_status, "CONFIRMED")
        self.assertTrue(AdminActionLog.objects.filter(action="Reviewed fraud alert", target_id=str(self.log.pk)).exists())

    def test_false_positive_clears_the_transaction(self):
        self.client.force_authenticate(self.support)
        self.client.post(f"/api/adminpanel/fraud-logs/{self.log.pk}/review/", {"resolution": "FALSE_POSITIVE"}, format="json")
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.fraud_status, "CLEARED")

    def test_review_rules(self):
        url = f"/api/adminpanel/fraud-logs/{self.log.pk}/review/"
        self.client.force_authenticate(self.read_only)
        self.assertEqual(self.client.post(url, {"resolution": "FALSE_POSITIVE"}, format="json").status_code, 403)
        self.client.force_authenticate(self.support)
        self.assertEqual(self.client.post(url, {"resolution": "MAYBE"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(url, {"resolution": "FALSE_POSITIVE"}, format="json").status_code, 200)
        self.assertEqual(self.client.post(url, {"resolution": "FALSE_POSITIVE"}, format="json").status_code, 409)
        self.assertEqual(self.client.post("/api/adminpanel/fraud-logs/999/review/", {"resolution": "FALSE_POSITIVE"}, format="json").status_code, 404)